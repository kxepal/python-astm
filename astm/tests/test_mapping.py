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
import unittest
import warnings
from astm import mapping
from astm.compat import u

class FieldTestCase(unittest.TestCase):

    def test_init_default(self):
        f = mapping.Field()
        self.assertTrue(hasattr(f, 'name'))
        self.assertTrue(hasattr(f, 'default'))
        self.assertEqual(f.name, None)
        self.assertEqual(f.default, None)

    def test_init_with_custom_name(self):
        f = mapping.Field(name='foo')
        self.assertEqual(f.name, 'foo')

    def test_init_with_custom_default_value(self):
        f = mapping.Field(default='foo')
        self.assertEqual(f.default, 'foo')

    def test_callable_default_value(self):
        class Dummy(mapping.Mapping):
            field = mapping.Field(default=lambda: 'foobar')
        self.assertEqual(Dummy().field, 'foobar')


class NotUsedFieldTestCase(unittest.TestCase):

    def setUp(self):
        class Dummy(mapping.Mapping):
            field = mapping.NotUsedField()
        self.Dummy = Dummy

    def test_get_value(self):
        obj = self.Dummy()
        self.assertEqual(obj.field, None)
        self.assertEqual(obj[0], None)

    def test_set_value(self):
        obj = self.Dummy()
        with warnings.catch_warnings(record=True) as w:
            obj.field = 42
            assert issubclass(w[-1].category, UserWarning)
        self.assertEqual(obj.field, None)


class IntegerTestCase(unittest.TestCase):

    def setUp(self):
        class Dummy(mapping.Mapping):
            field = mapping.IntegerField()
        self.Dummy = Dummy

    def test_get_value(self):
        obj = self.Dummy(field=42)
        self.assertEqual(obj.field, 42)

    def test_set_value(self):
        obj = self.Dummy()
        obj.field = 42
        self.assertEqual(obj.field, 42)

    def test_set_string_value(self):
        obj = self.Dummy()
        obj.field = '42'
        self.assertEqual(obj.field, 42)
        self.assertRaises(TypeError, setattr, obj, 'field', 'foo')


class DecimalFieldTestCase(unittest.TestCase):

    def setUp(self):
        class Dummy(mapping.Mapping):
            field = mapping.DecimalField()
        self.Dummy = Dummy

    def test_get_value(self):
        obj = self.Dummy(field=3.14)
        self.assertEqual(obj.field, decimal.Decimal('3.14'))

    def test_set_value(self):
        obj = self.Dummy()
        obj.field = 3.14
        self.assertEqual(obj.field, decimal.Decimal('3.14'))

    def test_set_int_value(self):
        obj = self.Dummy()
        obj.field = 42
        self.assertEqual(obj.field, decimal.Decimal('42'))


class TextFieldTestCase(unittest.TestCase):

    def setUp(self):
        class Dummy(mapping.Mapping):
            field = mapping.TextField()
        self.Dummy = Dummy

    def test_get_value(self):
        obj = self.Dummy(field='foo')
        self.assertEqual(obj.field, 'foo')

    def test_set_value(self):
        obj = self.Dummy()
        obj.field = u('привет')
        self.assertEqual(obj.field, u('привет'))

    def test_set_utf8_value(self):
        obj = self.Dummy()
        obj.field = u('привет').encode('utf-8')
        self.assertEqual(obj.field, u('привет'))

    def test_fail_set_non_utf8_value(self):
        obj = self.Dummy()
        try:
            obj.field = u('привет').encode('cp1251')
        except UnicodeDecodeError:
            pass
        else:
            self.fail('%s expected' % UnicodeDecodeError)

    def test_fail_set_non_string_value(self):
        obj = self.Dummy()
        try:
            obj.field = object()
        except TypeError:
            pass
        else:
            self.fail('%s expected' % TypeError)

    def test_raw_value(self):
        obj = self.Dummy()
        obj.field = u('привет')
        self.assertEqual(obj._data['field'], u('привет'))


class DateFieldTestCase(unittest.TestCase):

    def setUp(self):
        class Dummy(mapping.Mapping):
            field = mapping.DateField()
        self.Dummy = Dummy
        self.datetime = datetime.datetime(2009, 2, 13, 23, 31, 30)
        self.date = datetime.datetime(2009, 2, 13)

    def test_get_value(self):
        obj = self.Dummy(field=self.datetime)
        self.assertEqual(obj.field, self.date)

    def test_set_datetime_value(self):
        obj = self.Dummy()
        obj.field = self.datetime
        self.assertEqual(obj.field, self.date)

    def test_init_date_value(self):
        obj = self.Dummy(field=self.date)
        self.assertEqual(obj.field, self.date)

    def test_set_date_value(self):
        obj = self.Dummy()
        obj.field = self.date
        self.assertEqual(obj.field, self.date)

    def test_raw_value(self):
        obj = self.Dummy()
        obj.field = self.datetime
        self.assertEqual(obj._data['field'],
                         self.date.strftime(obj._fields[0][1].format))

    def test_set_string_value(self):
        obj = self.Dummy()
        obj.field = '20090213'
        self.assertRaises(ValueError, setattr, obj, 'field', '1234567')


class TimeFieldTestCase(unittest.TestCase):

    def setUp(self):
        class Dummy(mapping.Mapping):
            field = mapping.TimeField()
        self.Dummy = Dummy
        self.datetime = datetime.datetime(2009, 2, 13, 23, 31, 30)
        self.time = datetime.time(23, 31, 30)

    def test_get_value(self):
        obj = self.Dummy(field=self.datetime)
        self.assertEqual(obj.field, self.time)

    def test_set_datetime_value(self):
        obj = self.Dummy()
        obj.field = self.datetime
        self.assertEqual(obj.field, self.time)

    def test_init_time_value(self):
        obj = self.Dummy(field=self.time)
        self.assertEqual(obj.field, self.time)

    def test_set_time_value(self):
        obj = self.Dummy()
        obj.field = self.time
        self.assertEqual(obj.field, self.time)

    def test_raw_value(self):
        obj = self.Dummy()
        obj.field = self.datetime
        self.assertEqual(obj._data['field'],
                         self.time.strftime(obj._fields[0][1].format))

    def test_set_string_value(self):
        obj = self.Dummy()
        obj.field = '111213'
        self.assertRaises(ValueError, setattr, obj, 'field', '314159')


class DatetimeFieldTestCase(unittest.TestCase):

    def setUp(self):
        class Dummy(mapping.Mapping):
            field = mapping.DateTimeField()
        self.Dummy = Dummy
        self.datetime = datetime.datetime(2009, 2, 13, 23, 31, 30)
        self.date = datetime.datetime(2009, 2, 13)

    def test_get_value(self):
        obj = self.Dummy(field=self.datetime)
        self.assertEqual(obj.field, self.datetime)

    def test_set_value(self):
        obj = self.Dummy()
        obj.field = self.datetime
        self.assertEqual(obj.field, self.datetime)

    def test_get_date_value(self):
        obj = self.Dummy(field=self.date)
        self.assertEqual(obj.field, self.date)

    def test_set_date_value(self):
        obj = self.Dummy()
        obj.field = self.date
        self.assertEqual(obj.field, self.date)

    def test_raw_value(self):
        obj = self.Dummy()
        obj.field = self.datetime
        self.assertEqual(obj._data['field'],
                         self.datetime.strftime(obj._fields[0][1].format))

    def test_set_string_value(self):
        obj = self.Dummy()
        obj.field = '20090213233130'
        self.assertRaises(ValueError, setattr, obj, 'field', '12345678901234')


class ConstantFieldTestCase(unittest.TestCase):

    def test_get_value(self):
        class Dummy(mapping.Mapping):
            field = mapping.ConstantField(default=42)
        obj = Dummy()
        self.assertEqual(obj.field, 42)

    def test_set_value_if_none_default(self):
        class Dummy(mapping.Mapping):
            field = mapping.ConstantField(default='foo')
        obj = Dummy()
        obj.field = 'foo'
        self.assertEqual(obj.field, 'foo')

    def test_fail_override_setted_value(self):
        class Dummy(mapping.Mapping):
            field = mapping.ConstantField(default='foo')
        obj = Dummy()
        obj.field = 'foo'
        self.assertEqual(obj.field, 'foo')
        self.assertRaises(ValueError, setattr, obj, 'field', 'bar')

    def test_restrict_new_values_by_default_one(self):
        class Dummy(mapping.Mapping):
            field = mapping.ConstantField(default='foo')
        obj = Dummy()
        self.assertRaises(ValueError, setattr, obj, 'field', 'bar')
        obj.field = 'foo'
        self.assertEqual(obj.field, 'foo')

    def test_raw_value(self):
        class Dummy(mapping.Mapping):
            field = mapping.ConstantField(default='foo')
        obj = Dummy()
        obj.field = 'foo'
        self.assertEqual(obj._data['field'], 'foo')

    def test_raw_value_should_be_string(self):
        class Dummy(mapping.Mapping):
            field = mapping.ConstantField(default=42)
        obj = Dummy()
        obj.field = 42
        self.assertEqual(obj._data['field'], '42')

    def test_always_required(self):
        field = mapping.ConstantField(default='test')
        assert field.required
        self.assertRaises(TypeError, mapping.ConstantField, default='test', required=False)

    def test_default_value_should_be_defined(self):
        self.assertRaises(ValueError, mapping.ConstantField)


class SetFieldTestCase(unittest.TestCase):

    def setUp(self):
        class Dummy(mapping.Mapping):
            field = mapping.SetField(values=['foo', 'bar', 'baz'])
        self.Dummy = Dummy

    def test_get_value(self):
        obj = self.Dummy(field='foo')
        self.assertEqual(obj.field, 'foo')

    def test_set_value(self):
        obj = self.Dummy()
        obj.field = 'bar'
        self.assertEqual(obj.field, 'bar')

    def test_restrict_new_values_by_specified_set(self):
        obj = self.Dummy()
        self.assertRaises(ValueError, setattr, obj, 'field', 'boo')

    def test_reject_any_value(self):
        class Dummy(mapping.Mapping):
            field = mapping.SetField()
        obj = Dummy()
        self.assertRaises(ValueError, setattr, obj, 'field', 'bar')
        self.assertRaises(ValueError, setattr, obj, 'field', 'foo')
        obj.field = None

    def test_custom_field(self):
        class Dummy(mapping.Mapping):
            field = mapping.SetField(values=[1, 2, 3],
                                     field=mapping.IntegerField())
        obj = Dummy()
        obj.field = 1
        self.assertEqual(obj._data['field'], '1')
        obj.field = 2
        self.assertEqual(obj._data['field'], '2')
        obj.field = 3
        self.assertEqual(obj._data['field'], '3')


    def test_raw_value(self):
        obj = self.Dummy()
        obj.field = 'foo'
        self.assertEqual(obj._data['field'], 'foo')


class ComponentFieldTestCase(unittest.TestCase):

    def setUp(self):
        class Dummy(mapping.Mapping):
            field = mapping.ComponentField(
                mapping = mapping.Component.build(
                    mapping.Field(name='foo'),
                    mapping.IntegerField(name='bar'),
                    mapping.ConstantField(name='baz', default='42')
                )
            )
        self.Dummy = Dummy

    def test_get_value(self):
        obj = self.Dummy(field=['foo', 14, '42'])
        self.assertEqual(obj.field, ['foo', 14, '42'])

    def test_set_value(self):
        obj = self.Dummy()
        self.assertRaises(TypeError, setattr, obj, 'field', 42)
        self.assertRaises(ValueError, setattr, obj, 'field', [1, 2, 3])
        obj.field = ['test', 24, '42']
        self.assertEqual(obj.field, ['test', 24, '42'])

    def test_iter(self):
        obj = self.Dummy(field=['foo', 14, '42'])
        self.assertEqual(list(obj.field), ['foo', 14, '42'])

    def test_raw_value(self):
        obj = self.Dummy()
        obj.field = ['foo', 14, '42']
        self.assertEqual(obj._data['field'], ['foo', 14, '42'])

    def test_set_string_value(self):
        obj = self.Dummy()
        obj.field = 'foo'
        self.assertEqual(obj.field[0], 'foo')
        self.assertEqual(obj.field[1], None)
        self.assertEqual(obj.field[2], '42')


class RepeatedComponentFieldTestCase(unittest.TestCase):

    def setUp(self):
        class Dummy(mapping.Mapping):
            field = mapping.RepeatedComponentField(
                mapping.Component.build(
                    mapping.TextField(name='key'),
                    mapping.IntegerField(name='value'),
                )
            )
        class Thing(mapping.Mapping):
            numbers = mapping.RepeatedComponentField(
                mapping.Component.build(
                    mapping.IntegerField(name='value')
                )
            )
        self.Dummy = Dummy
        self.Thing = Thing

    def test_get_value(self):
        obj = self.Dummy(field=[['foo', 1], ['bar', 2], ['baz', 3]])
        self.assertEqual(obj.field, [['foo', 1], ['bar', 2], ['baz', 3]])

    def test_set_value(self):
        obj = self.Dummy()
        self.assertRaises(TypeError, setattr, obj, 'field', 42)
        obj.field = [['foo', 42]]
        self.assertEqual(obj.field, [['foo', 42]])

    def test_fail_on_set_strings(self):
        obj = self.Dummy()
        obj.field = 'foo' # WHY?
        #self.assertRaises(TypeError, setattr, obj, 'field', 'foo')

    def test_iter(self):
        obj = self.Dummy(field=[['foo', 14]])
        self.assertEqual(list(obj.field), [['foo', 14]])

    def test_getter_returns_list(self):
        obj = self.Dummy([['foo', 42]])
        self.assertTrue(isinstance(obj.field, list))

    def test_proxy_delitem(self):
        obj = self.Dummy([['foo', 1], ['bar', 2]])
        del obj.field[0]
        self.assertEqual(len(obj.field), 1)
        self.assertEqual(obj.field[0], ['bar', 2])

    def test_proxy_append(self):
        obj = self.Dummy([['foo', 1]])
        self.assertEqual(obj.field[0], ['foo', 1])
        obj.field.append(['bar', 2])
        self.assertEqual(obj.field[1], ['bar', 2])

    def test_proxy_extend(self):
        obj = self.Dummy([['foo', 1]])
        obj.field.extend([['bar', 2], ['baz', 3]])
        self.assertEqual(len(obj.field), 3)
        self.assertEqual(obj.field[2], ['baz', 3])

    def test_proxy_contains(self):
        obj = self.Thing(numbers=[[i] for i in range(5)])
        self.assertTrue([3] in obj.numbers)
        self.assertTrue([6] not in obj.numbers)

    def test_proxy_count(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        self.assertEqual(1, obj.numbers.count([1]))
        self.assertEqual(0, obj.numbers.count([4]))

    def test_proxy_index(self):
        obj = self.Thing(numbers=[[1], [2], [4]])
        self.assertEqual(1, obj.numbers.index([2]))

    def test_proxy_index_range(self):
        obj = self.Thing(numbers=[[1], [2], [4], [5]])
        self.assertEqual(2, obj.numbers.index([4], 2, 3))

    def test_fail_proxy_index_for_nonexisted_element(self):
        obj = self.Thing(numbers=[[1], [2], [4]])
        self.assertRaises(ValueError, obj.numbers.index, [5])

    def test_fail_proxy_index_negative_start(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        self.assertRaises(ValueError, obj.numbers.index, 2, -1 ,3)

    def test_proxy_insert(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        obj.numbers.insert(0, [0])
        self.assertEqual(obj.numbers[0], [0])

    def test_proxy_remove(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        obj.numbers.remove([1])
        obj.numbers.remove([2])
        self.assertEqual(len(obj.numbers), 1)
        self.assertEqual(obj.numbers[0].value, 3)

    def test_fail_proxy_remove_missing(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        self.assertRaises(ValueError, obj.numbers.remove, [5])

    def test_proxy_pop(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        self.assertEqual(obj.numbers.pop(), [3])
        self.assertEqual(len(obj.numbers), 2)
        self.assertEqual(obj.numbers.pop(0), [1])

    def test_proxy_slices(self):
        obj = self.Thing()
        obj.numbers = [[i] for i in range(5)]
        ll = obj.numbers[1:3]
        self.assertEqual(len(ll), 2)
        self.assertEqual(ll[0], [1])
        obj.numbers[2:4] = [[i] for i in range(6, 8)]
        self.assertEqual(obj.numbers[2], [6])
        self.assertEqual(obj.numbers[4], [4])
        self.assertEqual(len(obj.numbers), 5)
        del obj.numbers[3:]
        self.assertEquals(len(obj.numbers), 3)

    def test_proxy_sort_fails(self):
        class Dummy(mapping.Mapping):
            numbers = mapping.RepeatedComponentField(
                mapping.Component.build(
                    mapping.IntegerField(name='a'),
                    mapping.IntegerField(name='b')
                )
            )
        obj = Dummy(numbers=[[4, 2], [2, 3], [0, 1]])
        self.assertRaises(NotImplementedError, obj.numbers.sort)

    def test_proxy_lt(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        self.assertTrue(obj.numbers < [[4], [5], [6]])

    def test_proxy_lt_with_other_proxy(self):
        obj1 = self.Thing(numbers=[[1], [2], [3]])
        obj2 = self.Thing(numbers=[[4], [5], [6]])
        self.assertTrue(obj1.numbers < obj2.numbers)

    def test_proxy_le(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        self.assertTrue(obj.numbers <= [[1], [2], [3]])

    def test_proxy_le_with_other_proxy(self):
        obj1 = self.Thing(numbers=[[1], [2], [3]])
        obj2 = self.Thing(numbers=[[1], [2], [3]])
        self.assertTrue(obj1.numbers <= obj2.numbers)

    def test_proxy_eq(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        self.assertTrue(obj.numbers == [[1], [2], [3]])

    def test_proxy_eq_with_other_proxy(self):
        obj1 = self.Thing(numbers=[[1], [2], [3]])
        obj2 = self.Thing(numbers=[[1], [2], [3]])
        self.assertTrue(obj1.numbers == obj2.numbers)

    def test_proxy_ne(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        self.assertTrue(obj.numbers != [[4], [5], [6]])

    def test_proxy_ne_with_other_proxy(self):
        obj1 = self.Thing(numbers=[[1], [2], [3]])
        obj2 = self.Thing(numbers=[[4], [5], [6]])
        self.assertTrue(obj1.numbers != obj2.numbers)

    def test_proxy_ge(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        self.assertTrue(obj.numbers >= [[1], [2], [3]])

    def test_proxy_ge_with_other_proxy(self):
        obj1 = self.Thing(numbers=[[1], [2], [3]])
        obj2 = self.Thing(numbers=[[1], [2], [3]])
        self.assertTrue(obj1.numbers >= obj2.numbers)

    def test_proxy_gt(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        self.assertTrue(obj.numbers > [[0], [1], [2]])

    def test_proxy_gt_with_other_proxy(self):
        obj1 = self.Thing(numbers=[[1], [2], [3]])
        obj2 = self.Thing(numbers=[[0], [1], [2]])
        self.assertTrue(obj1.numbers > obj2.numbers)

    def test_proxy_add(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        l = obj.numbers + [[4], [5], [6]]
        self.assertEqual(l, [[1], [2], [3], [4], [5], [6]])
        self.assertTrue(isinstance(l, list))
        self.assertTrue(obj.numbers is not l)

    def test_proxy_add_other_proxy(self):
        obj1 = self.Thing(numbers=[[1], [2], [3]])
        obj2 = self.Thing(numbers=[[4], [5], [6]])
        l = obj1.numbers + obj2.numbers
        self.assertEqual(l, [[1], [2], [3], [4], [5], [6]])

    def test_proxy_iadd(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        obj.numbers += [[4], [5], [6]]
        self.assertEqual(obj.numbers, [[1], [2], [3], [4], [5], [6]])

    def test_proxy_mul(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        l = obj.numbers * 2
        self.assertEqual(l, [[1], [2], [3], [1], [2], [3]])
        self.assertTrue(isinstance(l, list))
        self.assertTrue(obj.numbers is not l)
        self.assertEqual(obj.numbers, [[1], [2], [3]])

    def test_proxy_mul_one(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        l = obj.numbers * 1
        self.assertEqual(l, [[1], [2], [3]])

    def test_proxy_mul_zero(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        l = obj.numbers * 0
        self.assertEqual(l, [])
        self.assertTrue(isinstance(l, list))

    def test_proxy_imul(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        obj.numbers *= 2
        self.assertEqual(obj.numbers, [[1], [2], [3], [1], [2], [3]])

    def test_proxy_imul_one(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        obj.numbers *= 1
        self.assertEqual(obj.numbers, [[1], [2], [3]])

    def test_proxy_imul_zero(self):
        obj = self.Thing(numbers=[[1], [2], [3]])
        obj.numbers *= 0
        self.assertEqual(obj.numbers, [])


class MappingTestCase(unittest.TestCase):

    def setUp(self):
        class Dummy(mapping.Mapping):
            foo = mapping.Field(default='bar')
            bar = mapping.ComponentField(mapping=mapping.Component.build(
                mapping.IntegerField(name='a'),
                mapping.IntegerField(name='b'),
                mapping.IntegerField(name='c'),
            ), default=[1,2,3])
        class Thing(mapping.Mapping):
            numbers = mapping.RepeatedComponentField(
                mapping.Component.build(
                    mapping.IntegerField(name='a'),
                    mapping.IntegerField(name='b')
                )
            )
        self.Dummy = Dummy
        self.Thing = Thing

    def test_equal(self):
        obj = self.Dummy('foo', [3, 2, 1])
        self.assertEqual(obj, ['foo', (3, 2, 1)])
        self.assertNotEqual(obj, ['foo'])

    def test_iter(self):
        obj = self.Dummy('foo', [3, 2, 1])
        self.assertEqual(list(obj), ['foo', [3, 2, 1]])

    def test_len(self):
        obj = self.Dummy('foo', [3, 2, 1])
        self.assertEqual(len(obj), 2)
        self.assertEqual(len(obj.bar), 3)

    def test_contains(self):
        obj = self.Dummy('foo', [3, 2, 1])
        assert 'foo' in obj

    def test_getitem(self):
        obj = self.Dummy('foo', [3, 2, 1])
        self.assertEqual(obj[1][0], 3)

    def test_setitem(self):
        obj = self.Dummy('foo', [3, 2, 1])
        obj[1][0] = 42
        self.assertEqual(obj[1][0], 42)

    def test_delitem(self):
        obj = self.Dummy('foo', [3, 2, 1])
        del obj[1][1]
        self.assertEqual(obj[1][1], None)

    def test_to_astm_record(self):
        obj = self.Dummy('foo', [3, 2, 1])
        self.assertEqual(obj.to_astm(), ['foo', ['3', '2', '1']])
        obj = self.Thing(numbers=[[4, 2], [2, 3], [0, 1]])
        self.assertEqual(obj.to_astm(), [[['4', '2'], ['2', '3'], ['0', '1']]])

    def test_required_field(self):
        class Dummy(mapping.Mapping):
            field = mapping.Field(required=True)
        obj = Dummy()
        self.assertTrue(obj.field is None)
        self.assertRaises(ValueError, obj.to_astm)

    def test_field_max_length(self):
        class Dummy(mapping.Mapping):
            field = mapping.Field(length=10)
        obj = Dummy()
        obj.field = '-' * 9
        obj.field = None
        obj.field = '-' * 10
        self.assertRaises(ValueError, setattr, obj, 'field', '-' * 11)


if __name__ == '__main__':
    unittest.main()
