# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import datetime
import decimal
import inspect
import time
import warnings
from operator import itemgetter
from itertools import islice
try:
    from itertools import izip_longest
except ImportError: # Python 3
    from itertools import zip_longest as izip_longest
    from .compat import basestring, unicode, long


def make_string(value):
    if isinstance(value, unicode):
        return value
    elif isinstance(value, bytes):
        return unicode(value, 'utf-8')
    else:
        return unicode(value)


class Field(object):
    """Base mapping field class."""
    def __init__(self, name=None, default=None, required=False, length=None):
        self.name = name
        self.default = default
        self.required = required
        self.length = length

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance._data.get(self.name)
        if value is not None:
            value = self._get_value(value)
        elif self.default is not None:
            default = self.default
            if hasattr(default, '__call__'):
                default = default()
            value = default
        return value

    def __set__(self, instance, value):
        if value is not None:
            value = self._set_value(value)
        instance._data[self.name] = value

    def _get_value(self, value):
        return value

    def _set_value(self, value):
        value = make_string(value)
        if self.length is not None and len(value) > self.length:
            raise ValueError('Field %r value is too long (max %d, got %d)'
                            '' % (self.name, self.length, len(value)))
        return value


class MetaMapping(type):

    def __new__(mcs, name, bases, d):
        fields = []
        names = []
        def merge_fields(items):
            for name, field in items:
                if field.name is None:
                    field.name = name
                if name not in names:
                    fields.append((name, field))
                    names.append(name)
                else:
                    fields[names.index(name)] = (name, field)
        for base in bases:
            if hasattr(base, '_fields'):
                merge_fields(base._fields)
        merge_fields([(k, v) for k, v in d.items() if isinstance(v, Field)])
        if '_fields' not in d:
            d['_fields'] = fields
        else:
            merge_fields(d['_fields'])
            d['_fields'] = fields
        return super(MetaMapping, mcs).__new__(mcs, name, bases, d)


_MappingProxy = MetaMapping('_MappingProxy', (object,), {}) # Python 3 workaround

class Mapping(_MappingProxy):

    def __init__(self, *args, **kwargs):
        fieldnames = map(itemgetter(0), self._fields)
        values = dict(izip_longest(fieldnames, args))
        values.update(kwargs)
        self._data = {}
        for attrname, field in self._fields:
            attrval = values.pop(attrname, None)
            if attrval is None:
                setattr(self, attrname, getattr(self, attrname))
            else:
                setattr(self, attrname, attrval)
        if values:
            raise ValueError('Unexpected kwargs found: %r' % values)

    @classmethod
    def build(cls, *a):
        fields = []
        newcls = type('Generic' + cls.__name__, (cls,), {})
        for field in a:
            if field.name is None:
                raise ValueError('Name is required for ordered fields.')
            setattr(newcls, field.name, field)
            fields.append((field.name, field))
        newcls._fields = fields
        return newcls

    def __getitem__(self, key):
        return self.values()[key]

    def __setitem__(self, key, value):
        setattr(self, self._fields[key][0], value)

    def __delitem__(self, key):
        self._data[self._fields[key][0]] = None

    def __iter__(self):
        return iter(self.values())

    def __contains__(self, item):
        return item in self.values()

    def __len__(self):
        return len(self._data)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for key, value in zip(self.keys(), other):
            if getattr(self, key) != value:
                return False
        return True

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join('%s=%r' % (key, value)
                                     for key, value in self.items()))

    def keys(self):
        return [key for key, field in self._fields]

    def values(self):
        return [getattr(self, key) for key in self.keys()]

    def items(self):
        return [(key, getattr(self, key)) for key, field in self._fields]

    def to_astm(self):
        def values(obj):
            for key, field in obj._fields:
                value = obj._data[key]
                if isinstance(value, Mapping):
                    yield list(values(value))
                elif isinstance(value, list):
                    stack = []
                    for item in value:
                        if isinstance(item, Mapping):
                            stack.append(list(values(item)))
                        else:
                            stack.append(item)
                    yield stack
                elif value is None and field.required:
                    raise ValueError('Field %r value should not be None' % key)
                else:
                    yield value
        return list(values(self))


class Record(Mapping):
    """ASTM record mapping class."""


class Component(Mapping):
    """ASTM component mapping class."""


class TextField(Field):
    """Mapping field for string values."""
    def _set_value(self, value):
        if not isinstance(value, basestring):
            raise TypeError('String value expected, got %r' % value)
        return super(TextField, self)._set_value(value)


class ConstantField(Field):
    """Mapping field for constant values.

    >>> class Record(Mapping):
    ...     type = ConstantField(default='S')
    >>> rec = Record()
    >>> rec.type
    'S'
    >>> rec.type = 'W'
    Traceback (most recent call last):
        ...
    ValueError: Field changing not allowed
    """
    def __init__(self, name=None, default=None, field=Field()):
        super(ConstantField, self).__init__(name, default, True, None)
        self.field = field
        self.required = True
        if self.default is None:
            raise ValueError('Constant value should be defined')

    def _get_value(self, value):
        return self.default

    def _set_value(self, value):
        value = self.field._get_value(value)
        if self.default != value:
            raise ValueError('Field changing not allowed: got %r, accepts %r'
                            '' % (value, self.default))
        return super(ConstantField, self)._set_value(value)


class IntegerField(Field):
    """Mapping field for integer values."""
    def _get_value(self, value):
        return int(value)

    def _set_value(self, value):
        if not isinstance(value, (int, long)):
            try:
                value = self._get_value(value)
            except Exception:
                raise TypeError('Integer value expected, got %r' % value)
        return super(IntegerField, self)._set_value(value)


class DecimalField(Field):
    """Mapping field for decimal values."""
    def _get_value(self, value):
        return decimal.Decimal(value)

    def _set_value(self, value):
        if not isinstance(value, (int, long, float, decimal.Decimal)):
            raise TypeError('Decimal value expected, got %r' % value)
        return super(DecimalField, self)._set_value(value)


class DateField(Field):
    """Mapping field for storing date/time values."""
    format = '%Y%m%d'
    def _get_value(self, value):
        return datetime.datetime.strptime(value, self.format)

    def _set_value(self, value):
        if isinstance(value, basestring):
            value = self._get_value(value)
        if not isinstance(value, (datetime.datetime, datetime.date)):
            raise TypeError('Datetime value expected, got %r' % value)
        return value.strftime(self.format)


class TimeField(Field):
    """Mapping field for storing times."""
    format = '%H%M%S'
    def _get_value(self, value):
        if isinstance(value, basestring):
            try:
                value = value.split('.', 1)[0] # strip out microseconds
                value = datetime.time(*time.strptime(value, self.format)[3:6])
            except ValueError:
                raise ValueError('Value %r does not match format %s'
                                 '' % (value, self.format))
        return value

    def _set_value(self, value):
        if isinstance(value, basestring):
            value = self._get_value(value)
        if not isinstance(value, (datetime.datetime, datetime.time)):
            raise TypeError('Datetime value expected, got %r' % value)
        if isinstance(value, datetime.datetime):
            value = value.time()
        return value.replace(microsecond=0).strftime(self.format)


class DateTimeField(Field):
    """Mapping field for storing date/time values."""
    format = '%Y%m%d%H%M%S'
    def _get_value(self, value):
        return datetime.datetime.strptime(value, self.format)

    def _set_value(self, value):
        if isinstance(value, basestring):
            value = self._get_value(value)
        if not isinstance(value, (datetime.datetime, datetime.date)):
            raise TypeError('Datetime value expected, got %r' % value)
        return value.strftime(self.format)


class SetField(Field):
    """Mapping field for predefined set of values."""
    def __init__(self, name=None, default=None,
                 required=False, length=None,
                 values=None, field=Field()):
        super(SetField, self).__init__(name, default, required, length)
        self.field = field
        self.values = values and set(values) or set([])

    def _get_value(self, value):
        return self.field._get_value(value)

    def _set_value(self, value):
        value = self.field._get_value(value)
        if value not in self.values:
            raise ValueError('Unexpectable value %r' % value)
        return self.field._set_value(value)


class ComponentField(Field):
    """Mapping field for storing record component."""
    def __init__(self, mapping, name=None, default=None):
        self.mapping = mapping
        default = default or mapping()
        super(ComponentField, self).__init__(name, default)


    def _get_value(self, value):
        if isinstance(value, dict):
            return self.mapping(**value)
        elif isinstance(value, self.mapping):
            return value
        else:
            return self.mapping(*value)

    def _set_value(self, value):
        if isinstance(value, dict):
            return self.mapping(**value)
        elif isinstance(value, self.mapping):
            return value
        if isinstance(value, basestring):
            value = [value]
        return self.mapping(*value)


class RepeatedComponentField(Field):
    """Mapping field for storing list of record components."""
    def __init__(self, field, name=None, default=None):
        if isinstance(field, ComponentField):
            self.field = field
        else:
            assert isinstance(field, type) and issubclass(field, Mapping)
            self.field = ComponentField(field)
        default = default or []
        super(RepeatedComponentField, self).__init__(name, default)

    class Proxy(list):
        def __init__(self, seq, field):
            list.__init__(self, seq)
            self.list = seq
            self.field = field

        def _to_list(self):
            return [list(self.field._get_value(item)) for item in self.list]

        def __add__(self, other):
            obj = type(self)(self.list, self.field)
            obj.extend(other)
            return obj

        def __iadd__(self, other):
            self.extend(other)
            return self

        def __mul__(self, other):
            return type(self)(self.list * other, self.field)

        def __imul__(self, other):
            self.list *= other
            return self

        def __lt__(self, other):
            return self._to_list() < other

        def __le__(self, other):
            return self._to_list() <= other

        def __eq__(self, other):
            return self._to_list() == other

        def __ne__(self, other):
            return self._to_list() != other

        def __ge__(self, other):
            return self._to_list() >= other

        def __gt__(self, other):
            return self._to_list() > other

        def __repr__(self):
            return '<ListProxy %s %r>' % (self.list, list(self))

        def __str__(self):
            return str(self.list)

        def __unicode__(self):
            return unicode(self.list)

        def __delitem__(self, index):
            del self.list[index]

        def __getitem__(self, index):
            return self.field._get_value(self.list[index])

        def __setitem__(self, index, value):
            self.list[index] = self.field._set_value(value)

        def __delslice__(self, i, j):
            del self.list[i:j]

        def __getslice__(self, i, j):
            return self.__class__(self.list[i:j], self.field)

        def __setslice__(self, i, j, seq):
            self.list[i:j] = [self.field._set_value(v) for v in seq]

        def __contains__(self, value):
            for item in self:
                if item == value:
                    return True
            return False

        def __iter__(self):
            for index in range(len(self)):
                yield self[index]

        def __len__(self):
            return len(self.list)

        def __nonzero__(self):
            return bool(self.list)

        def __reduce__(self):
            return self.list.__reduce__()

        def __reduce_ex__(self, *args, **kwargs):
            return self.list.__reduce_ex__(*args, **kwargs)

        def append(self, item):
            self.list.append(self.field._set_value(item))

        def count(self, value):
            return self._to_list().count(value)

        def extend(self, other):
            self.list.extend([self.field._set_value(i) for i in other])

        def index(self, value, start=None, stop=None):
            start = start or 0
            for idx, item in enumerate(islice(self, start, stop)):
                if item == value:
                    return idx + start
            else:
                raise ValueError('%r not in list' % value)

        def insert(self, index, object):
            self.list.insert(index, self.field._set_value(object))

        def remove(self, value):
            for item in self:
                if item == value:
                    return self.list.remove(value)
            raise ValueError('Value %r not in list' % value)

        def pop(self, index=-1):
            return self.field._get_value(self.list.pop(index))

        def sort(self, cmp=None, key=None, reverse=False):
            raise NotImplementedError('In place sorting not allowed.')

    # update docstrings from list
    for name, obj in inspect.getmembers(Proxy):
        if getattr(list, name, None) is None\
        or name in ['__module__', '__doc__']:
            continue
        if not inspect.isfunction(obj):
            continue
        obj.__doc__ = getattr(list, name).__doc__
    del name, obj

    def _get_value(self, value):
        return self.Proxy(value, self.field)

    def _set_value(self, value):
        return [self.field._set_value(item) for item in value]


class NotUsedField(Field):
    """Mapping field for value that should be used. Acts as placeholder.
    On attempt to assign something to it raises :exc:`UserWarning` and rejects
    assigned value."""
    def __init__(self, name=None):
        super(NotUsedField, self).__init__(name)

    def _get_value(self, value):
        return None

    def _set_value(self, value):
        warnings.warn('Field %r is not used, any assignments are omitted'
                      '' % self.name, UserWarning)
        return None
