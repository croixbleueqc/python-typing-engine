Typing Engine
=============

A Python package for a Typing Engine.

Main purpose is to translate dict/json to a typing object with transformation, getter, setter, validation support...

Installation
------------

This package is available for Python 3.5+.

Install the development version from source:

.. code:: bash

    pip3 install .

Dev with Typing version 2
-------------------------

Quick example
^^^^^^^^^^^^^

.. code:: python

    from typing-engine.base.typing import Typing2, Field

    class Test(Typing2):
        name1 = Field() \
                    .default("coucou")

    class Test2(Test):
        def setter_int1_1(self, value):
            print("int1 %s, value %s" % (str(self.int1), str(value)))
            return 10 if value is None else value + 10

        def getter_bool1(self, value):
            print("GETTER from TEST2")
            if value is not None and value == True:
                return "This is true !"
            return value

        bool1 = Field(default=True).getters(getter_bool1)
        listing = Field().list_of(inside_instanciator=Test)
        int1 = Field().converter(loads=int, dumps=str).setters(setter_int1_1)

    class Test3(Test2):
        int2 = Field().converter(loads=int).setters(Test2.setter_int1_1)

        @classmethod
        def transform_fields(cls):
            super().transform_fields()
            cls.bool1.default(False).getters(Test3.getter_bool1)
            cls.int1.setters(cls.setter_int1_1)

        def getter_bool1(self, value):
            print("GETTER from TEST3")
            if value is not None and value == True:
                return "TEST3 : This is true !"
            return value

    class Test4(Typing2):
        def getter_int1_bis(self, value):
            if self.parent:
                return self.parent.int1
            return value

        int1_bis = Field().getters(getter_int1_bis)


    t1 = Test()
    t2 = Test2()
    t3 = Test3()
    t4 = Test4()
    t4.parent = t3

    t3.int1 = 20
    t3.int1

    t4.int1_bis = 0
    t4.int1_bis
    type(t4).int1_bis.direct_get(t4)

    t1.dumps()
    t2.dumps()
    t3.dumps()
    t4.dumps()

Field
^^^^^

All functionnalties are now provided by the Field class.

You can read the tests/test_base_field or tests/test_base_typing2 to have an overview of all posibilities
