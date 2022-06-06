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


class BaseTyping2Test(unittest.TestCase):
    def test_isolation(self):
        """Check isolation of static fields with inheritance"""

        class T1(Typing2):
            name1 = Field()

        class T2(T1):
            pass

        t1 = T1()
        t2 = T2()
        self.assertNotEqual(T1.name1, T2.name1)

        # NOTE: looks like the same than before but take a look on instanciation order
        class T3(Typing2):
            name1 = Field()

        class T4(T1):
            pass

        t4 = T4()
        t3 = T3()
        self.assertNotEqual(T3.name1, T4.name1)

    def test_base_typing2(self):
        class T(Typing2):
            pass

        class C(Typing2):
            name1 = Field()

        data = {"name1": "1", "name2": "value2", "name3": [{"name1": "value1"}]}

        # Empty definition

        t = T()

        self.assertEqual(t.dumps(), {})
        self.assertEqual(t.dumps(raw=True), {})

        t.loads_from_dict(data)

        self.assertEqual(t.dumps(), {})
        self.assertEqual(t.dumps(raw=True), {})

        t2 = T(t)

        self.assertEqual(t2.dumps(), {})
        self.assertEqual(t2.dumps(raw=True), {})

        # add new Fields

        t = T()
        T.name1 = Field(name="name1")
        T.name2 = Field(name="name2")
        T.name3 = Field(name="name3").list_of()
        T._Typing2__fields.append(T.name1)
        T._Typing2__fields.append(T.name2)
        T._Typing2__fields.append(T.name3)

        t.loads_from_dict(data)

        self.assertIsInstance(t.name3, list)
        self.assertEqual(
            t.dumps(), {"name1": "1", "name2": "value2", "name3": [{"name1": "value1"}]}
        )
        self.assertEqual(
            t.dumps(raw=True),
            {"name1": "1", "name2": "value2", "name3": [{"name1": "value1"}]},
        )

        t.reset()
        self.assertEqual(t.dumps(), {"name1": None, "name2": None, "name3": []})

        T.name3.list_of(inside_instanciator=C)
        t.loads_from_dict(data)

        self.assertIsInstance(t.name3[0], C)
        self.assertEqual(t.name3[0].dumps(), {"name1": "value1"})
        self.assertEqual(
            t.dumps(), {"name1": "1", "name2": "value2", "name3": [{"name1": "value1"}]}
        )

        # Remove a field

        t.reset()

        T._Typing2__fields.remove(T.name2)
        del T.name2
        t.loads_from_dict(data)

        self.assertEqual(t.dumps(), {"name1": "1", "name3": [{"name1": "value1"}]})

        # Hide field

        T.name1.hide()

        self.assertEqual(t.dumps(), {"name3": [{"name1": "value1"}]})
        self.assertEqual(
            t.dumps(raw=True), {"name1": "1", "name3": [{"name1": "value1"}]}
        )

        # Mapping Field

        T.name3.mapping("list")

        self.assertEqual(t.dumps(), {"list": [{"name1": "value1"}]})
        self.assertEqual(
            t.dumps(raw=True), {"name1": "1", "name3": [{"name1": "value1"}]}
        )

        self.assertIsNotNone(t.get_field("name3"))
        self.assertIsNotNone(t.get_field("list"))

        # Converter Field

        T.name1.unhide()
        t.reset()

        self.assertEqual(t.dumps(), {"name1": None, "list": []})

        t.loads_from_dict(data)

        self.assertIsInstance(t.name1, str)

        T.name1.converter(loads=int, dumps=str)
        t.loads_from_dict(data)

        self.assertIsInstance(t.name1, int)
        self.assertIsInstance(t.dumps()["name1"], str)
        self.assertIsInstance(t.dumps(raw=True)["name1"], int)

        # Default value

        T.name1.default(0)
        t.reset()

        self.assertEqual(t.name1, 0)

        T.name1.default(None)
        t.reset()
        self.assertEqual(t.name1, None)

        # Setter
        def func1(instance, value):
            return value + 10

        T.name1.setters(func1)
        T.name1.setters(func1)
        t.name1 = 10

        self.assertEqual(t.name1, 30)

        # Getter
        def func2(instance, value):
            return "0" + str(value)

        T.name1.getters(func2)

        self.assertEqual(t.name1, "030")

    def test_encode_decode(self):
        class T(Typing2):
            test = Field().mapping("Test")

        t = T()
        t.test = 20

        # Encode

        self.assertEqual(t.encode(), b'{"test": 20}')

        # Decode

        t = T()
        t.loads_from_bytes(b'{"test": 20}')
        self.assertEqual(t.dumps(), {"Test": 20})

        t = T(b'{"test": 30}')
        self.assertEqual(t.dumps(), {"Test": 30})
