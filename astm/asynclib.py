# -*- coding: utf-8 -*-
#
# Author: Sam Rushing <rushing@nightmare.com>
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""
.. module:: astm.asynclib
   :synopsis: Forked version of asyncore mixed with asynchat.
.. moduleauthor:: Sam Rushing <rushing@nightmare.com>
.. sectionauthor:: Christopher Petrilli <petrilli@amber.org>
.. sectionauthor:: Steve Holden <sholden@holdenweb.com>
.. heavily adapted from original documentation by Sam Rushing
"""

import heapq
import logging
import os
import select
import socket
import sys
import time
from collections import deque
from errno import (
    EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, EINVAL,
    ENOTCONN, ESHUTDOWN, EINTR, EISCONN, EBADF, ECONNABORTED, EPIPE, EAGAIN,
    errorcode
)
from .compat import long, b, bytes, buffer

class ExitNow(Exception):
    pass


_DISCONNECTED = frozenset((ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED, EPIPE,
                           EBADF))

_RERAISEABLE_EXC = (ExitNow, KeyboardInterrupt, SystemExit)

_SOCKET_MAP = {}

_SCHEDULED_TASKS = []

log = logging.getLogger(__name__)


def _strerror(err):
    try:
        return os.strerror(err)
    except (ValueError, OverflowError, NameError):
        if err in errorcode:
            return errorcode[err]
        return "Unknown error %s" % err


def read(obj):
    """Triggers ``handle_read_event`` for specified object."""
    try:
        obj.handle_read_event()
    except _RERAISEABLE_EXC:
        raise
    except Exception:
        obj.handle_error()


def write(obj):
    """Triggers ``handle_write_event`` for specified object."""
    try:
        obj.handle_write_event()
    except _RERAISEABLE_EXC:
        raise
    except Exception:
        obj.handle_error()


def exception(obj):
    """Triggers ``handle_exception_event`` for specified object."""
    try:
        obj.handle_exception_event()
    except _RERAISEABLE_EXC:
        raise
    except Exception:
        obj.handle_error()


def readwrite(obj, flags):
    try:
        if flags & select.POLLIN:
            obj.handle_read_event()
        if flags & select.POLLOUT:
            obj.handle_write_event()
        if flags & select.POLLPRI:
            obj.handle_exception_event()
        if flags & (select.POLLHUP | select.POLLERR | select.POLLNVAL):
            obj.handle_close()
    except socket.error as e:
        if e.args[0] not in _DISCONNECTED:
            obj.handle_error()
        else:
            obj.handle_close()
    except _RERAISEABLE_EXC:
        raise
    except Exception:
        obj.handle_error()


def poll(timeout=0.0, map=None):
    if map is None:
        map = map or _SOCKET_MAP
    if map:
        r = []; w = []; e = []
        for fd, obj in map.items():
            is_r = obj.readable()
            is_w = obj.writable()
            if is_r:
                r.append(fd)
                # accepting sockets should not be writable
            if is_w and not obj.accepting:
                w.append(fd)
            if is_r or is_w:
                e.append(fd)
        if [] == r == w == e:
            time.sleep(timeout)
            return

        try:
            r, w, e = select.select(r, w, e, timeout)
        except select.error as err:
            if err.args[0] != EINTR:
                raise
            else:
                return

        for fd in r:
            obj = map.get(fd)
            if obj is None:
                continue
            read(obj)

        for fd in w:
            obj = map.get(fd)
            if obj is None:
                continue
            write(obj)

        for fd in e:
            obj = map.get(fd)
            if obj is None:
                continue
            exception(obj)


def scheduler(tasks=None):
    if tasks is None:
        tasks = _SCHEDULED_TASKS
    now = time.time()
    while tasks and now >= tasks[0].timeout:
        call = heapq.heappop(tasks)
        if call.repush:
            heapq.heappush(tasks, call)
            call.repush = False
            continue
        try:
            call.call()
        finally:
            if not call.cancelled:
                call.cancel()


def loop(timeout=30.0, map=None, tasks=None, count=None):
    """
    Enter a polling loop that terminates after count passes or all open
    channels have been closed. All arguments are optional. The *count*
    parameter defaults to None, resulting in the loop terminating only when all
    channels have been closed. The *timeout* argument sets the timeout
    parameter for the appropriate :func:`select` or :func:`poll` call, measured
    in seconds; the default is 30 seconds. The *use_poll* parameter, if true,
    indicates that :func:`poll` should be used in preference to :func:`select`
    (the default is ``False``).

    The *map* parameter is a dictionary whose items are the channels to watch.
    As channels are closed they are deleted from their map. If *map* is
    omitted, a global map is used. Channels (instances of
    :class:`asyncore.dispatcher`, :class:`asynchat.async_chat` and subclasses
    thereof) can freely be mixed in the map.

    """
    if map is None:
        map = _SOCKET_MAP
    if tasks is None:
        tasks = _SCHEDULED_TASKS

    if count is None:
        while map or tasks:
            if map:
                poll(timeout, map)
            if tasks:
                scheduler()

    else:
        while (map or tasks) and count > 0:
            if map:
                poll(timeout, map)
            if tasks:
                scheduler()
            count -= 1


class call_later:
    """Calls a function at a later time.

    It can be used to asynchronously schedule a call within the polling
    loop without blocking it. The instance returned is an object that
    can be used to cancel or reschedule the call.
    """

    def __init__(self, seconds, target, *args, **kwargs):
        """
        - seconds: the number of seconds to wait
        - target: the callable object to call later
        - args: the arguments to call it with
        - kwargs: the keyword arguments to call it with
        - _tasks: a reserved keyword to specify a different list to
          store the delayed call instances.
        """
        assert callable(target), "%s is not callable" % target
        assert seconds >= 0, \
            "%s is not greater than or equal to 0 seconds" % (seconds)
        self.__delay = seconds
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.__tasks = kwargs.pop('_tasks', _SCHEDULED_TASKS)
        # seconds from the epoch at which to call the function
        self.timeout = time.time() + self.__delay
        self.repush = False
        self.cancelled = False
        heapq.heappush(self.__tasks, self)

    def __lt__(self, other):
        return self.timeout <= other.timeout

    def call(self):
        """Call this scheduled function."""
        assert not self.cancelled, "Already cancelled"
        self.__target(*self.__args, **self.__kwargs)

    def reset(self):
        """Reschedule this call resetting the current countdown."""
        assert not self.cancelled, "Already cancelled"
        self.timeout = time.time() + self.__delay
        self.repush = True

    def delay(self, seconds):
        """Reschedule this call for a later time."""
        assert not self.cancelled, "Already cancelled."
        assert seconds >= 0, \
            "%s is not greater than or equal to 0 seconds" % (seconds)
        self.__delay = seconds
        newtime = time.time() + self.__delay
        if newtime > self.timeout:
            self.timeout = newtime
            self.repush = True
        else:
            # XXX - slow, can be improved
            self.timeout = newtime
            heapq.heapify(self.__tasks)

    def cancel(self):
        """Unschedule this call."""
        assert not self.cancelled, "Already cancelled"
        self.cancelled = True
        del self.__target, self.__args, self.__kwargs
        if self in self.__tasks:
            pos = self.__tasks.index(self)
            if pos == 0:
                heapq.heappop(self.__tasks)
            elif pos == len(self.__tasks) - 1:
                self.__tasks.pop(pos)
            else:
                self.__tasks[pos] = self.__tasks.pop()
                heapq._siftup(self.__tasks, pos)


class Dispatcher(object):
    """
    The :class:`Dispatcher` class is a thin wrapper around a low-level socket
    object. To make it more useful, it has a few methods for event-handling
    which are called from the asynchronous loop. Otherwise, it can be treated
    as a normal non-blocking socket object.

    The firing of low-level events at certain times or in certain connection
    states tells the asynchronous loop that certain higher-level events have
    taken place. For example, if we have asked for a socket to connect to
    another host, we know that the connection has been made when the socket
    becomes writable for the first time (at this point you know that you may
    write to it with the expectation of success). The implied higher-level
    events are:

    +----------------------+----------------------------------------+
    | Event                | Description                            |
    +======================+========================================+
    | ``handle_connect()`` | Implied by the first read or write     |
    |                      | event                                  |
    +----------------------+----------------------------------------+
    | ``handle_close()``   | Implied by a read event with no data   |
    |                      | available                              |
    +----------------------+----------------------------------------+
    | ``handle_accept()``  | Implied by a read event on a listening |
    |                      | socket                                 |
    +----------------------+----------------------------------------+

    During asynchronous processing, each mapped channel's :meth:`readable` and
    :meth:`writable` methods are used to determine whether the channel's socket
    should be added to the list of channels :c:func:`select`\ ed or
    :c:func:`poll`\ ed for read and write events.

    """

    connected = False
    accepting = False
    addr = None

    def __init__(self, sock=None, map=None):
        if map is None:
            self._map = _SOCKET_MAP
        else:
            self._map = map

        self._fileno = None
        if sock:
            # Set to nonblocking just to make sure for cases where we
            # get a socket from a blocking source.
            sock.setblocking(0)
            self.set_socket(sock, map)
            self.connected = True
            # The constructor no longer requires that the socket
            # passed be connected.
            try:
                self.addr = sock.getpeername()
            except socket.error as err:
                if err.args[0] == ENOTCONN:
                    # To handle the case where we got an unconnected
                    # socket.
                    self.connected = False
                else:
                    # The socket is broken in some unknown way, alert
                    # the user and remove it from the map (to prevent
                    # polling of broken sockets).
                    self._del_channel(map)
                    raise
        else:
            self.socket = None

    def __repr__(self):
        status = [self.__class__.__module__ + '.' + self.__class__.__name__]
        if self.accepting and self.addr:
            status.append('listening')
        elif self.connected:
            status.append('connected')
        if self.addr is not None:
            try:
                status.append('%s:%d' % self.addr)
            except TypeError:
                status.append(repr(self.addr))
        return '<%s at %#x>' % (' '.join(status), id(self))

    __str__ = __repr__

    def _add_channel(self, map=None):
        log.debug('Adding channel %s' % self)
        if map is None:
            map = self._map
        map[self._fileno] = self

    def _del_channel(self, map=None):
        fd = self._fileno
        if map is None:
            map = self._map
        if fd in map:
            log.debug('Closing channel %d:%s' % (fd, self))
            del map[fd]
        self._fileno = None

    def create_socket(self, family, type):
        """
        This is identical to the creation of a normal socket, and will use
        the same options for creation. Refer to the :mod:`socket` documentation
        for information on creating sockets.
        """
        self.family_and_type = family, type
        sock = socket.socket(family, type)
        sock.setblocking(0)
        self.set_socket(sock)

    def set_socket(self, sock, map=None):
        self.socket = sock
        self._fileno = sock.fileno()
        self._add_channel(map)

    def set_reuse_addr(self):
        try:
            self.socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR,
                self.socket.getsockopt(socket.SOL_SOCKET,
                                       socket.SO_REUSEADDR) | 1
            )
        except socket.error:
            pass

    def readable(self):
        """
        Called each time around the asynchronous loop to determine whether a
        channel's socket should be added to the list on which read events can
        occur. The default method simply returns ``True``, indicating that by
        default, all channels will be interested in read events."""
        return True

    def writable(self):
        """
        Called each time around the asynchronous loop to determine whether a
        channel's socket should be added to the list on which write events can
        occur. The default method simply returns ``True``, indicating that by
        default, all channels will be interested in write events.
        """
        return True

    def listen(self, num):
        """Listen for connections made to the socket.

        The `num` argument specifies the maximum number of queued connections
        and should be at least 1; the maximum value is system-dependent
        (usually 5)."""
        self.accepting = True
        if os.name == 'nt' and num > 5:
            num = 5
        return self.socket.listen(num)

    def bind(self, address):
        """Bind the socket to `address`.

        The socket must not already be bound. The format of `address` depends
        on the address family --- refer to the :mod:`socket` documentation for
        more information. To mark the socket as re-usable (setting the
        :const:`SO_REUSEADDR` option), call the :class:`Dispatcher` object's
        :meth:`set_reuse_addr` method.
        """
        self.addr = address
        return self.socket.bind(address)

    def connect(self, address):
        """
        As with the normal socket object, `address` is a tuple with the first
        element the host to connect to, and the second the port number.
        """
        self.connected = False
        self.addr = address
        err = self.socket.connect_ex(address)
        if err in (EINPROGRESS, EALREADY, EWOULDBLOCK)\
        or err == EINVAL and os.name in ('nt', 'ce'):
            return
        if err in (0, EISCONN):
            self.handle_connect_event()
        else:
            raise socket.error(err, errorcode[err])

    def accept(self):
        """Accept a connection.

        The socket must be bound to an address and listening for connections.
        The return value can be either ``None`` or a pair ``(conn, address)``
        where `conn` is a *new* socket object usable to send and receive data on
        the connection, and *address* is the address bound to the socket on the
        other end of the connection.

        When ``None`` is returned it means the connection didn't take place, in
        which case the server should just ignore this event and keep listening
        for further incoming connections.
        """
        try:
            conn, addr = self.socket.accept()
        except TypeError:
            return None
        except socket.error as err:
            if err.args[0] in (EWOULDBLOCK, ECONNABORTED, EAGAIN):
                return None
            else:
                raise
        else:
            return conn, addr

    def send(self, data):
        """Send `data` to the remote end-point of the socket."""
        try:
            log.debug('[%s:%d] <<< %r', self.addr[0], self.addr[1], data)
            result = self.socket.send(data)
            return result
        except socket.error as err:
            if err.args[0] == EWOULDBLOCK:
                return 0
            elif err.args[0] in _DISCONNECTED:
                self.handle_close()
                return 0
            else:
                raise

    def recv(self, buffer_size):
        """Read at most `buffer_size` bytes from the socket's remote end-point.

        An empty string implies that the channel has been closed from the other
        end.
        """
        try:
            data = self.socket.recv(buffer_size)
            log.debug('[%s:%d] >>> %r', self.addr[0], self.addr[1], data)
            if not data:
                # a closed connection is indicated by signaling
                # a read condition, and having recv() return 0.
                self.handle_close()
                return b''
            else:
                return data
        except socket.error as err:
            # winsock sometimes throws ENOTCONN
            if err.args[0] in _DISCONNECTED:
                self.handle_close()
                return b''
            else:
                raise

    def close(self):
        """Close the socket.
        
        All future operations on the socket object will fail.
        The remote end-point will receive no more data (after queued data is
        flushed). Sockets are automatically closed when they are
        garbage-collected.
        """
        self.connected = False
        self.accepting = False
        self._del_channel()
        try:
            self.socket.close()
        except socket.error as err:
            if err.args[0] not in (ENOTCONN, EBADF):
                raise

    def handle_read_event(self):
        if self.accepting:
            # accepting sockets are never connected, they "spawn" new
            # sockets that are connected
            self.handle_accept()
        elif not self.connected:
            self.handle_connect_event()
            self.handle_read()
        else:
            self.handle_read()

    def handle_connect_event(self):
        err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err != 0:
            raise socket.error(err, _strerror(err))
        self.handle_connect()
        self.connected = True

    def handle_write_event(self):
        if self.accepting:
            # Accepting sockets shouldn't get a write event.
            # We will pretend it didn't happen.
            return

        if not self.connected:
            #check for errors
            err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err != 0:
                raise socket.error(err, _strerror(err))

            self.handle_connect_event()
        self.handle_write()

    def handle_exception_event(self):
        # handle_exception_event() is called if there might be an error on the
        # socket, or if there is OOB data
        # check for the error condition first
        err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err != 0:
            # we can get here when select.select() says that there is an
            # exceptional condition on the socket
            # since there is an error, we'll go ahead and close the socket
            # like we would in a subclassed handle_read() that received no
            # data
            self.handle_close()
        else:
            self.handle_exception()

    def handle_error(self):
        """
        Called when an exception is raised and not otherwise handled.
        The default version prints a condensed traceback.
        """
        try:
            self_repr = repr(self)
        except Exception:
            self_repr = '<__repr__(self) failed for object at %0x>' % id(self)

        log.exception('Uncatched python exception, closing channel %s',
                      self_repr)

        self.handle_close()

    def handle_exception(self):
        log.exception('Unknown error')

    def handle_read(self):
        log.debug('Unhandled read event')

    def handle_write(self):
        """
        Called when the asynchronous loop detects that a writable socket can be
        written. Often this method will implement the necessary buffering for
        performance. For example::

            def handle_write(self):
                sent = self.send(self.buffer)
                self.buffer = self.buffer[sent:]
        """
        log.debug('Unhandled write event')

    def handle_connect(self):
        """
        Called when the active opener's socket actually makes a connection.
        Might send a "welcome" banner, or initiate a protocol negotiation with
        the remote endpoint, for example.
        """
        log.info('[%s:%d] Connection established', self.addr[0], self.addr[1])

    def handle_accept(self):
        """
        Called on listening channels (passive openers) when a connection can be
        established with a new remote endpoint that has issued a :meth:`connect`
        call for the local endpoint.
        """
        log.info('[%s:%d] Connection accepted', self.addr[0], self.addr[1])

    def handle_close(self):
        """Called when the socket is closed."""
        log.info('[%s:%d] Connection closed', self.addr[0], self.addr[1])
        self.close()


def close_all(map=None, tasks=None, ignore_all=False):
    if map is None:
        map = _SOCKET_MAP
    if tasks is None:
        tasks = _SCHEDULED_TASKS
    for x in list(map.values()):
        try:
            x.close()
        except OSError as err:
            if err.args[0] == EBADF:
                pass
            elif not ignore_all:
                raise
        except _RERAISEABLE_EXC:
            raise
        except Exception:
            if not ignore_all:
                raise
    map.clear()

    for x in tasks:
        try:
            x.cancel()
        except _RERAISEABLE_EXC:
            raise
        except Exception:
            if not ignore_all:
                raise
    del tasks[:]


class AsyncChat(Dispatcher):
    """
    This class is an abstract subclass of :class:`Dispatcher`. To make
    practical use of the code you must subclass :class:`AsyncChat`, providing
    meaningful meth:`found_terminator` method.
    The :class:`Dispatcher` methods can be used, although not all make
    sense in a message/response context.

    Like :class:`Dispatcher`, :class:`AsyncChat` defines a set of
    events that are generated by an analysis of socket conditions after a
    :c:func:`select` call. Once the polling loop has been started the
    :class:`AsyncChat` object's methods are called by the event-processing
    framework with no action on the part of the programmer.
    """

    # these are overridable defaults

    #: The asynchronous input buffer size.
    recv_buffer_size = 4096
    #: The asynchronous output buffer size.
    send_buffer_size = 4096

    #: Encoding usage is not enabled by default, because that is a
    #: sign of an application bug that we don't want to pass silently.
    use_encoding = False
    #: Default encoding.
    encoding = 'latin-1'

    #: Remove terminator from the result data.
    strip_terminator = True

    _terminator = None

    def __init__(self, sock=None, map=None):
        # for string terminator matching
        self._input_buffer = b''
        self.inbox = deque()
        self.outbox = deque()
        super(AsyncChat, self).__init__(sock, map)
        self.collect_incoming_data = self.pull
        self.initiate_send = self.flush

    def pull(self, data):
        """Puts `data` into incoming queue. Also available by alias
        `collect_incoming_data`.
        """
        self.inbox.append(data)

    def found_terminator(self):
        """
        Called when the incoming data stream  matches the :attr:`termination`
        condition. The default method, which must be overridden, raises a
        :exc:`NotImplementedError` exception. The buffered input data should be
        available via an instance attribute.
        """
        raise NotImplementedError("must be implemented in subclass")

    def _set_terminator(self, term):
        self._terminator = term

    def _get_terminator(self):
        return self._terminator

    #: The input delimiter and the terminating condition to be recognized on the
    #: channel. May be any of three types of value, corresponding to three
    #: different ways to handle incoming protocol data.
    #:
    #: +-----------+---------------------------------------------+
    #: | term      | Description                                 |
    #: +===========+=============================================+
    #: | *string*  | Will call :meth:`found_terminator` when the |
    #: |           | string is found in the input stream         |
    #: +-----------+---------------------------------------------+
    #: | *integer* | Will call :meth:`found_terminator` when the |
    #: |           | indicated number of characters have been    |
    #: |           | received                                    |
    #: +-----------+---------------------------------------------+
    #: | ``None``  | The channel continues to collect data       |
    #: |           | forever                                     |
    #: +-----------+---------------------------------------------+
    #:
    #: Note that any data following the terminator will be available for reading
    #: by the channel after :meth:`found_terminator` is called.
    terminator = property(_get_terminator, _set_terminator)

    def handle_read(self):
        try:
            data = self.recv(self.recv_buffer_size)
        except socket.error as err:
            self.handle_error()
            return

        if self.use_encoding and not isinstance():
            data = data.decode(self.encoding)

        self._input_buffer += data

        while self._input_buffer:
            terminator = self.terminator
            if not terminator:
                handler = self._lookup_none_terminator
            elif isinstance(terminator, (int, long)):
                handler = self._lookup_int_terminator
            elif isinstance(terminator, str):
                handler = self._lookup_str_terminator
            else:
                handler = self._lookup_list_terminator
            res = handler(self.terminator)
            if res is None:
                break

    def _lookup_none_terminator(self, terminator):
        self.pull(self._input_buffer)
        self._input_buffer = ''
        return False

    def _lookup_int_terminator(self, terminator):
        if len(self._input_buffer) < terminator:
            self.pull(self._input_buffer)
            self._input_buffer = ''
            return False
        else:
            self.pull(self._input_buffer[:terminator])
            self._input_buffer = self._input_buffer[terminator:]
            self.found_terminator()
            return True

    def _lookup_list_terminator(self, terminator):
        for item in terminator:
            if self._input_buffer.find(item) != -1:
                return self._lookup_str_terminator(item)
        return self._lookup_none_terminator(terminator)

    def _lookup_str_terminator(self, terminator):
        # 3 cases:
        # 1) end of buffer matches terminator exactly:
        #    collect data, transition
        # 2) end of buffer matches some prefix:
        #    collect data to the prefix
        # 3) end of buffer does not match any prefix:
        #    collect data
        terminator_len = len(terminator)
        index = self._input_buffer.find(terminator)
        if index != -1:
            # we found the terminator
            if self.strip_terminator and index > 0:
                self.pull(self._input_buffer[:index])
            elif not self.strip_terminator:
                self.pull(self._input_buffer[:index+terminator_len])
            self._input_buffer = self._input_buffer[index+terminator_len:]
            # This does the Right Thing if the terminator is changed here.
            self.found_terminator()
            return True
        else:
            # check for a prefix of the terminator
            index = find_prefix_at_end(self._input_buffer, terminator)
            if index:
                if index != len(self._input_buffer):
                    # we found a prefix, collect up to the prefix
                    self.pull(self._input_buffer[:-index])
                    self._input_buffer = self._input_buffer[-index:]
                return None
            else:
                # no prefix, collect it all
                self.pull(self._input_buffer)
                self._input_buffer = ''
                return False

    def handle_write(self):
        self.flush()

    def push(self, data):
        """
        Pushes data on to the channel's fifo to ensure its transmission.
        This is all you need to do to have the channel write the data out to
        the network.
        """
        sabs = self.send_buffer_size
        if len(data) > sabs:
            for i in range(0, len(data), sabs):
                self.outbox.append(data[i:i+sabs])
        else:
            self.outbox.append(data)
        return self.flush()

    def push_with_producer(self, producer):
        self.outbox.append(producer)
        return self.flush()

    def readable(self):
        """Predicate for inclusion in the readable for select()"""
        return True

    def writable(self):
        """Predicate for inclusion in the writable for select()"""
        # For nonblocking sockets connect() will not set self.connected flag,
        # due to EINPROGRESS socket error which is actually promise for
        # successful connection.
        return bool(self.outbox or not self.connected)

    def close_when_done(self):
        """Automatically close this channel once the outgoing queue is empty."""
        self.outbox.append(None)

    def flush(self):
        """Sends all data from outgoing queue."""
        while self.outbox and self.connected:
            self._send_chunky(self.outbox.popleft())

    def _send_chunky(self, data):
        """Sends data as chunks sized by ``send_buffer_size`` value.

        Returns ``True`` on success, ``False`` on error and ``None`` on closing
        event.
        """
        if self.use_encoding and not isinstance(data, bytes):
            data = data.encode(self.encoding)
        while True:
            if data is None:
                self.handle_close()
                return

            obs = self.send_buffer_size
            bdata = buffer(data, 0, obs)

            try:
                num_sent = self.send(bdata)
            except socket.error:
                self.handle_error()
                return False

            if num_sent and num_sent < len(bdata) or obs < len(data):
                data = data[num_sent:]
            else:
                return True

    def discard_buffers(self):
        """In emergencies this method will discard any data held in the input
        and output buffers."""
        self.discard_input_buffers()
        self.discard_output_buffers()

    def discard_input_buffers(self):
        self._input_buffer = b('')
        self.inbox.clear()

    def discard_output_buffers(self):
        self.outbox.clear()


def find_prefix_at_end(haystack, needle):
    l = len(needle) - 1
    while l and not haystack.endswith(needle[:l]):
        l -= 1
    return l
