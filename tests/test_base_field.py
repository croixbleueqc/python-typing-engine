"""Typing class test"""

# Copyright 2019 mickybart

# This file is part of python-typing-engine.

# python-typing-engine is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# python-typing-engine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with python-typing-engine.  If not, see <https://www.gnu.org/licenses/>.


import unittest

from typing_engine.typing import Field, Typing2


class BaseFieldTest(unittest.TestCase):
    def test_init(self):
        f = Field()
        self.assertIsInstance(f, Field)

        f = Field(name="LIST", instanciator=list)
        self.assertEqual(f.name, "LIST")
        self.assertEqual(f.instance_name, "_LIST")
        self.assertEqual(f.instanciator, list)

    def test_get(self):
        f = Field(name="NAME")

        def func1(instance, value):
            return "OTHER"

        f.getters(func1)

        instance = Typing2()
        instance._NAME = 10

        self.assertEqual(f.direct_get(instance), 10)

        self.assertEqual(f.__get__(instance, None), "OTHER")

        f.default(33)
        self.assertEqual(instance._NAME, 10)

        del instance._NAME
        self.assertEqual(f.__get__(instance, None), "OTHER")
        self.assertEqual(instance._NAME, 33)

        f.getters(clear=True)
        self.assertEqual(f.__get__(instance, None), 33)

    def test_set(self):
        f = Field(name="NAME")

        def func1(instance, value):
            return value + 10

        f.setters(func1)
        f.setters(func1)

        instance = Typing2()

        f.direct_set(instance, 10)
        self.assertEqual(instance._NAME, 10)

        f.__set__(instance, 40)
        self.assertEqual(instance._NAME, 60)

        f.setters(clear=True)
        f.__set__(instance, 40)
        self.assertEqual(instance._NAME, 40)

    def test_delete(self):
        f = Field(name="NAME")

        instance = Typing2()

        f.direct_set(instance, 10)
        self.assertEqual(instance._NAME, 10)

        f.__delete__(instance)
        self.assertEqual(getattr(instance, "_NAME", "DONOTEXIST"), "DONOTEXIST")

    def test_get_name(self):
        f = Field(name="NAME")
        f.mapping("PRETTY_NAME")

        self.assertEqual(f.get_name(), "PRETTY_NAME")
        self.assertEqual(f.get_name(no_mapping=True), "NAME")

    def test_setters(self):
        f = Field(name="NAME")

        def func1(instance, value):
            return value

        def func2(instance, value):
            return value

        f.setters(func1)
        self.assertEqual(f.setters_funcs[0], func1)

        f.setters(func2)
        self.assertEqual(f.setters_funcs[0], func1)
        self.assertEqual(f.setters_funcs[1], func2)

        f.setters(clear=True)
        self.assertEqual(len(f.setters_funcs), 0)

    def test_getters(self):
        f = Field(name="NAME")

        def func1(instance, value):
            return value

        def func2(instance, value):
            return value

        f.getters(func1)
        self.assertEqual(f.getters_funcs[0], func1)

        f.getters(func2)
        self.assertEqual(f.getters_funcs[0], func2)
        self.assertEqual(f.getters_funcs[1], func1)

        f.getters(clear=True)
        self.assertEqual(len(f.getters_funcs), 0)

    def test_mapping(self):
        f = Field(name="NAME")
        f.mapping("PRETTY_NAME")

        self.assertEqual(f.mapping_name, "PRETTY_NAME")

    def test_list_of(self):
        f = Field(name="NAME")
        f.list_of()
        self.assertIsNone(f.inside_instanciator)
        self.assertEqual(f.instanciator, list)
        self.assertEqual(f.is_list, True)

        f.list_of(inside_instanciator=dict)
        self.assertEqual(f.inside_instanciator, dict)

    def test_hide(self):
        f = Field(name="NAME")
        f.hide()

        self.assertEqual(f.hidden, True)

        f.unhide()

        self.assertEqual(f.hidden, False)

    def test_default(self):
        f = Field(name="NAME", default="name_value")
        self.assertEqual(f.default_value, "name_value")

        f.default(None)
        self.assertEqual(f.default_value, None)

    def test_converter(self):
        f = Field(name="NAME")
        f.converter(loads=int, dumps=str)

        self.assertEqual(f.loads_converter, int)
        self.assertEqual(f.dumps_converter, str)

    def test_match(self):
        f = Field(name="NAME")
        f.mapping("PRETTY_NAME")

        self.assertEqual(f.match("NAME"), True)
        self.assertEqual(f.match("PRETTY_NAME"), True)
        self.assertEqual(f.match("OTHER"), False)

    def test_get_instance(self):
        f = Field(name="NAME")
        self.assertIsNone(f.get_instance(None))

        f.default("coucou")
        self.assertEqual(f.get_instance(None), "coucou")

    def test_get_inside_instance(self):
        f = Field(name="NAME")
        f.list_of(inside_instanciator=dict)

        value = f.get_inside_instance({"data": "DATA"}, None)
        self.assertIsInstance(value, dict)
        self.assertEqual(value, {"data": "DATA"})

        f.list_of()
        value = f.get_inside_instance("data", None)
        self.assertIsInstance(value, str)
        self.assertEqual(value, "data")

    def test_loads_convert(self):
        f = Field(name="NAME")
        f.converter(loads=int)

        self.assertIsNone(f.loads_convert(None))

        value = f.loads_convert(10)
        self.assertIsInstance(value, int)
        self.assertEqual(value, 10)

        value = f.loads_convert("10")
        self.assertIsInstance(value, int)
        self.assertEqual(value, 10)

        self.assertRaises(ValueError, f.loads_convert, "not a number")

    def test_dumps_convert(self):
        f = Field(name="NAME")
        f.converter(dumps=int)

        self.assertIsNone(f.dumps_convert(None))

        value = f.dumps_convert("10")
        self.assertIsInstance(value, int)
        self.assertEqual(value, 10)

        value = f.dumps_convert(10)
        self.assertIsInstance(value, int)
        self.assertEqual(value, 10)

        self.assertRaises(ValueError, f.dumps_convert, "not a number")
