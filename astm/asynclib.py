# -*- coding: utf-8 -*-
#
# Author: Sam Rushing <rushing@nightmare.com>
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import logging
import os
import select
import socket
import time
from collections import deque
from errno import (
    EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, EINVAL,
    ENOTCONN, ESHUTDOWN, EINTR, EISCONN, EBADF, ECONNABORTED, EPIPE, EAGAIN,
    errorcode
)
from .compat import long, b, unicode, bytes, buffer

class ExitNow(Exception):
    pass


_DISCONNECTED = frozenset((ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED, EPIPE,
                           EBADF))

_RERAISEABLE_EXC = (ExitNow, KeyboardInterrupt, SystemExit)

_SOCKET_MAP = {}


log = logging.getLogger(__name__)


def _strerror(err):
    try:
        return os.strerror(err)
    except (ValueError, OverflowError, NameError):
        if err in errorcode:
            return errorcode[err]
        return "Unknown error %s" %err

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
    """Triggers ``handle_read_event`` for specified object."""
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

def loop(timeout=30.0, map=None, count=None):
    if map is None:
        map = _SOCKET_MAP

    if count is None:
        while map:
            poll(timeout, map)

    else:
        while map and count > 0:
            poll(timeout, map)
            count -= 1


class Dispatcher(object):

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
        return True

    def writable(self):
        return True

    def listen(self, num):
        self.accepting = True
        if os.name == 'nt' and num > 5:
            num = 5
        return self.socket.listen(num)

    def bind(self, addr):
        self.addr = addr
        return self.socket.bind(addr)

    def connect(self, address):
        self.connected = False
        err = self.socket.connect_ex(address)
        if err in (EINPROGRESS, EALREADY, EWOULDBLOCK)\
        or err == EINVAL and os.name in ('nt', 'ce'):
            return
        if err in (0, EISCONN):
            self.addr = address
            self.handle_connect_event()
        else:
            raise socket.error(err, errorcode[err])

    def accept(self):
        # XXX can return either an address pair or None
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
        try:
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
        try:
            data = self.socket.recv(buffer_size)
            if not data:
                # a closed connection is indicated by signaling
                # a read condition, and having recv() return 0.
                self.handle_close()
                return ''
            else:
                return data
        except socket.error as err:
            # winsock sometimes throws ENOTCONN
            if err.args[0] in _DISCONNECTED:
                self.handle_close()
                return ''
            else:
                raise

    def close(self):
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
        log.debug('Unhandled write event')

    def handle_connect(self):
        log.debug('Unhandled connect event')

    def handle_accept(self):
        pass

    def handle_close(self):
        self.close()


def close_all(map=None, ignore_all=False):
    if map is None:
        map = _SOCKET_MAP
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


class AsyncChat(Dispatcher):
    """This is an abstract class.  You must derive from this class, and add
    the two methods collect_incoming_data() and found_terminator()"""

    # these are overridable defaults

    recv_buffer_size = 4096
    send_buffer_size = 4096

    # we don't want to enable the use of encoding by default, because that is a
    # sign of an application bug that we don't want to pass silently

    use_encoding = False
    encoding = 'utf-8'

    def __init__(self, sock=None, map=None):
        # for string terminator matching
        self._input_buffer = ''
        self.inbox = deque()
        self.outbox = deque()
        super(AsyncChat, self).__init__(sock, map)

    def collect_incoming_data(self, data):
        self.inbox.append(data)

    def found_terminator(self):
        raise NotImplementedError("must be implemented in subclass")

    def _set_terminator(self, term):
        """Set the input delimiter.
        Can be a fixed string of any length, an integer, or None."""
        self._terminator = term

    def _get_terminator(self):
        return self._terminator

    terminator = property(_get_terminator, _set_terminator)

    def handle_read(self):
        try:
            data = self.recv(self.recv_buffer_size)
        except socket.error as err:
            self.handle_error()
            return

        if isinstance(data, bytes) and self.use_encoding:
            data = data.decode(self.encoding)

        self._input_buffer += data

        while self._input_buffer:
            lb = len(self._input_buffer)
            terminator = self.terminator
            if not terminator:
                # no terminator, collect it all
                self.collect_incoming_data(self._input_buffer)
                self._input_buffer = ''
            elif isinstance(terminator, (int, long)):
                # numeric terminator
                n = terminator
                if lb < n:
                    self.collect_incoming_data(self._input_buffer)
                    self._input_buffer = ''
                    self.terminator -= self.terminator
                else:
                    self.collect_incoming_data(self._input_buffer[:n])
                    self._input_buffer = self._input_buffer[n:]
                    self.terminator = 0
                    self.found_terminator()
            else:
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
                    if index > 0:
                        # don't bother reporting the empty string (source of subtle bugs)
                        self.collect_incoming_data(self._input_buffer[:index])
                    self._input_buffer = self._input_buffer[index+terminator_len:]
                    # This does the Right Thing if the terminator is changed here.
                    self.found_terminator()
                else:
                    # check for a prefix of the terminator
                    index = find_prefix_at_end(self._input_buffer, terminator)
                    if index:
                        if index != lb:
                            # we found a prefix, collect up to the prefix
                            self.collect_incoming_data(self._input_buffer[:-index])
                            self._input_buffer = self._input_buffer[-index:]
                        break
                    else:
                        # no prefix, collect it all
                        self.collect_incoming_data(self._input_buffer)
                        self._input_buffer = ''

    def handle_write(self):
        self.initiate_send()

    def push(self, data):
        sabs = self.send_buffer_size
        if len(data) > sabs:
            for i in range(0, len(data), sabs):
                self.outbox.append(data[i:i+sabs])
        else:
            self.outbox.append(data)
        self.initiate_send()

    def push_with_producer(self, producer):
        self.outbox.append(producer)
        self.initiate_send()

    def readable(self):
        """Predicate for inclusion in the readable for select()"""
        return True

    def writable(self):
        """Predicate for inclusion in the writable for select()"""
        return bool(self.outbox and self.connected)

    def close_when_done(self):
        """"Automatically close this channel once the outgoing queue is empty"""
        self.outbox.append(None)

    def initiate_send(self):
        while self.outbox and self.connected:
            first = self.outbox[0]
            # handle empty string/buffer or None entry
            if not first:
                del self.outbox[0]
                if first is None:
                    self.handle_close()
                    return

            obs = self.send_buffer_size
            data = buffer(first, 0, obs)

            # send the data
            try:
                num_sent = self.send(data)
            except socket.error:
                self.handle_error()
                return

            if num_sent:
                if num_sent < len(data) or obs < len(first):
                    self.outbox[0] = first[num_sent:]
                else:
                    del self.outbox[0]
                # we tried to send some actual data
            return

    def discard_buffers(self):
        self._input_buffer = b('')
        self.outbox.clear()


def find_prefix_at_end(haystack, needle):
    l = len(needle) - 1
    while l and not haystack.endswith(needle[:l]):
        l -= 1
    return l


# Asynchronous File I/O:
#
# After a little research (reading man pages on various unixen, and
# digging through the linux kernel), I've determined that select()
# isn't meant for doing asynchronous file i/o.
# Heartening, though - reading linux/mm/filemap.c shows that linux
# supports asynchronous read-ahead.  So _MOST_ of the time, the data
# will be sitting in memory for us already when we go to read it.
#
# What other OS's (besides NT) support async file i/o?  [VMS?]
#
# Regardless, this is useful for pipes, and stdin/stdout...

if os.name == 'posix':
    import fcntl

    class FileWrapper(object):
        # Here we override just enough to make a file
        # look like a socket for the purposes of asyncore.
        # The passed fd is automatically os.dup()'d

        def __init__(self, fd):
            self.fd = os.dup(fd)

        def recv(self, *args):
            return os.read(self.fd, *args)

        def send(self, *args):
            return os.write(self.fd, *args)

        def getsockopt(self, level, optname, buflen=None):
            if (level == socket.SOL_SOCKET and
                optname == socket.SO_ERROR and
                not buflen):
                return 0
            raise NotImplementedError('Only asyncore specific behaviour'
                                      ' implemented.')

        read = recv
        write = send

        def close(self):
            os.close(self.fd)

        def fileno(self):
            return self.fd

    class FileDispatcher(Dispatcher):

        def __init__(self, fd, map=None):
            super(FileDispatcher, self).__init__(map=map)
            self.connected = True
            try:
                fd = fd.fileno()
            except AttributeError:
                pass
            self.set_file(fd)
            # set it to non-blocking mode
            flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
            flags = flags | os.O_NONBLOCK
            fcntl.fcntl(fd, fcntl.F_SETFL, flags)

        def set_file(self, fd):
            self.socket = FileWrapper(fd)
            self._fileno = self.socket.fileno()
            self._add_channel()
