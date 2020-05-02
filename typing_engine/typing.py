"""Typing"""

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


import threading
import io, csv, json
from .errors import UnsupportedOperation

class Typing2:
    """Typing class version 2

    Constructor

    Keyword Arguments:
        data (object): Data input for typing
    """
    __init_lock = threading.Lock()

    def __init__(self, data=None, parent=None):
        self.parent = parent
        self.__one_time_init()
        self.post_init()

        if data is None:
            return
        elif isinstance(data, Typing2):
            self.loads_from_typing(data)
        elif isinstance(data, dict):
            self.loads_from_dict(data)
        elif isinstance(data, bytes):
            self.loads_from_bytes(data)

    def post_init(self):
        """Post __init__()

        Permit to run some code during __init__()
        and before loads()
        """
        pass

    def __one_time_init(self):
        """One time init (class init)

        - copy inherited fields inside top class
        - set names on all fields
        - set __fields list for internal use
        - transform_fields
        """

        top_cls = type(self)

        # First attempt without global lock to know if the class is already configured
        if top_cls.__dict__.get("_Typing2__init_done", False):
            # Already initialized so we don't need to run it again
            # as all configuration are set at the class level and shared between
            # all instances
            return

        with self.__init_lock:

            # Second attempt
            # as between the first test and the lock.acquire() someone else
            # can have already initialized the class.
            if top_cls.__dict__.get("_Typing2__init_done", False):
                return

            top_cls.__fields = []

            for cls in self.__class__.__mro__[:-1]:
                for name, field in cls.__dict__.items():
                    if isinstance(field, Field):
                        if cls == top_cls:
                            field.set_name(name)
                            top_cls.__fields.append(field)
                        elif self.get_field(name) is None:
                            copied_field = field.copy()
                            copied_field.set_name(name)
                            top_cls.__fields.append(copied_field)
                            setattr(top_cls, name, copied_field)

            self.transform_fields()

            # init done
            top_cls.__init_done = True

    def __dump(self, value, raw, is_list):
        """Export a specific value

        Recursive function mainly used for dumps()

        Args:
            value (object): A value to dump
            raw (bool): True - to expose a raw object
            is_list (bool): True - this is a list or assimilate

        Returns:
            object: A value
        """
        if is_list:
            values = []
            for i in value:
                # list of list is not supported so is_list need to be set to False
                values.append(self.__dump(i, raw, False))
            return values
        elif isinstance(value, Typing2):
            return value.dumps(raw)
        else:
            return value

    @classmethod
    def transform_fields(cls):
        """Transform fields

        Called during __init__() to override some previous or
        inherited static fields.

        eg:
            cls.<field>.hide()
        """
        pass

    def get_field(self, name):
        """Get the field configuration

        Arg:
            name (str): name of a field (can be the mapping name too)
        """
        for field in self.__fields:
            if field.match(name):
                return field

        return None

    def get_fields(self):
        """Get all fields

        Return:
            List: List of Field
        """
        return self.__fields

    def reset(self):
        """Reinitialize an object based on its definition"""
        for field in self.get_fields():
            field.__delete__(self)

    def loads_from_typing(self, other):
        """Loads from another object

        Args:
            other (Typing2): a Typing object
        """
        # no needs to call pre_loads() and post_loads as it will be done
        # by loads_from_dict
        self.loads_from_dict(other.dumps(raw=True))

    def pre_loads(self, data):
        """called before loads()

        Args:
            data (dict): A dictionary of data

        Returns:
            dict: data modified or identical
        """
        return data

    def loads_from_dict(self, data):
        """Loads from data

        Args:
            data (dict): A dictionary of data
        """
        if not data:
            return

        preload_data = self.pre_loads(data)

        for name, value in preload_data.items():
            field = self.get_field(name)

            if field is None:
                continue

            variable = getattr(self, field.name)

            if isinstance(variable, Typing2):
                variable.loads_from_dict(value)
            elif field.is_list:
                # we assume that value is enumerable as we need to store it on a list or equivalent
                for subset_data in value:
                    variable.append(field.get_inside_instance(subset_data, self))
            else:
                setattr(self, field.name, value)

        self.post_loads()

    def post_loads(self):
        """called after loads()"""
        pass

    def pre_dumps(self, raw):
        """called before dumps()

        Args:
            raw (bool): True - to expose a raw object
        """
        pass

    def dumps(self, raw=False):
        """Export as a dict

        Keyword Arguments:
            raw (bool): True - to expose a raw object

        Returns:
            dict: A dictionary of exposed fields
        """

        self.pre_dumps(raw)

        dump = dict()
        for field in self.get_fields():

            if not raw and field.hidden:
                continue

            value = getattr(self, field.name, None)

            if not raw:
                value = field.dumps_convert(value)

            dump[field.get_name(no_mapping=raw)] = self.__dump(value, raw, field.is_list)

        self.post_dumps(raw, dump)

        return dump

    def post_dumps(self, raw, dump):
        """called before returning dump from dumps()

        Last chance to transform a dump without overriding dumps()

        Args:
            raw (bool): True - to expose a raw object
            dump (dict): The dict from dumps()
        """
        pass

    def dumps_as_csv(self, raw=False, include_header=False, writer=None, dialect="unix"):
        """Export as a CSV

        Keyword Arguments:
            raw (bool): True - to expose a raw dumps
            include_header (bool): True - export the header, False - export data only
            writer (object): any object with a write() method
            dialect (str): unix|excel|excel-tab

        Returns:
            str: the csv content only if writer is not set
        """
        return_csv = writer is None

        if return_csv:
            writer = io.StringIO()

        dump = self.dumps(raw=raw)
        csv_writer = csv.DictWriter(writer, dump.keys(), dialect=dialect, quoting=csv.QUOTE_NONNUMERIC)
        if include_header:
            csv_writer.writeheader()
        csv_writer.writerow(dump)

        if return_csv:
            writer.flush()
            return writer.getvalue()

    def dump_as_json(self, raw=False):
        """Export as a json

        Keyword Arguments:
            raw (bool): True - to expose a raw dumps

        Returns:
            str: the json content
        """
        return json.dumps(
            self.dumps(raw=raw)
        )

    def encode(self, encoding="utf-8", errors="strict"):
        """Encode as bytes

        Returns:
            bytes: encoded typing
        """
        return json.dumps(self.dumps(raw=True)).encode(encoding=encoding, errors=errors)

    def loads_from_bytes(self, data, encoding="utf-8", errors="strict"):
        """Decode bytes to typing

        Args:
            data (bytes): a bytes representation
        """
        self.loads_from_dict(json.loads(data.decode(encoding=encoding, errors=errors)))

    def __str__(self):
        return str(self.dumps())

class Field:
    """Field

    Constructor

    Keyword Arguments:
        name (str): name of the field
        instanciator (class|function): a class or function that will instanciate an object
        default (object): a default value for the field
    """
    def __init__(self, name=None, instanciator=None, default=None):
        # from variables
        self.name = None
        self.instanciator = instanciator
        self.default_value = default

        # internal
        self.inside_instanciator = None
        self.is_list = False
        self.hidden = False
        self.mapping_name = None
        self.dumps_converter = None
        self.loads_converter = None
        self.instance_name = None
        self.setters_funcs = list()
        self.getters_funcs = list()

        self.set_name(name)

    def __get__(self, instance, owner):
        """Getter"""
        if instance is None:
            return self

        try:
            value = getattr(instance, self.instance_name)
        except AttributeError:
            # Set a temporary value without using setters
            # only because a setter can request a getattr on the field that
            # we are currently trying to set (avoid loop)
            setattr(instance, self.instance_name, None)

            # we can use setter safely without loop risk
            self.__set__(instance, self.get_instance(instance))

            # Call itself to return value and used getters as expected
            return self.__get__(instance, owner)

        # getters
        for func in self.getters_funcs:
            if (type(func).__name__ == "method"):
                # dynamic
                value = func(value)
            else:
                # static
                value = func(instance, value)

        return value

    def __set__(self, instance, value):
        """Setter

        Can convert value if loads converter is set.
        """
        value = self.loads_convert(value)
        for func in self.setters_funcs:
            if (type(func).__name__ == "method"):
                # dynamic
                value = func(value)
            else:
                # static
                value = func(instance, value)

        setattr(instance, self.instance_name, value)

    def __delete__(self, instance):
        """Deleter"""
        try:
            delattr(instance, self.instance_name)
        except AttributeError:
            pass

    def direct_set(self, instance, value, bypass_converter=False):
        """Set the value directly

        Args:
            instance (object): an object
            value (object): the value to set

        Keyword Arguments:
            bypass_converter (bool): True - Bypass the converter and not only setters
        """
        if not bypass_converter:
            value = self.loads_convert(value)
        setattr(instance, self.instance_name, value)

    def direct_get(self, instance):
        """Get the value directly

        Args:
            instance (object): an object

        Returns:
            object: the value
        """
        return getattr(instance, self.instance_name)

    def copy(self):
        """Create a copy of this field

        Returns:
            Field: a field copy
        """
        field = type(self)()

        field.name = self.name
        field.instanciator = self.instanciator
        field.inside_instanciator = self.inside_instanciator
        field.is_list = self.is_list
        field.default_value = self.default_value
        field.hidden = self.hidden
        field.mapping_name = self.mapping_name
        field.dumps_converter = self.dumps_converter
        field.loads_converter = self.loads_converter
        field.instance_name = self.instance_name
        for func in self.setters_funcs:
            field.setters(func)
        for func in self.getters_funcs:
            field.getters(func)

        return field

    def set_name(self, name):
        """Set the name and instance name

        Args:
            name (str): name of the field
        """
        self.name = name

        if name:
            self.instance_name = "_" + name
        else:
            self.instance_name = None

    def get_name(self, no_mapping=False):
        """Get the name or mapping name

        Keyword Arguments:
            no_mapping (bool): False - Prefer the mapping name
        """
        if not no_mapping and self.mapping_name is not None:
            return self.mapping_name

        return self.name

    def setters(self, function=None, clear=False):
        """add a new setter function

        Keyword Arguments:
            function (function): a function that get a value and return a new one
            clear (bool): True - purge all previous functions

        Returns:
            Field: self
        """
        if clear:
            self.setters_funcs.clear()
        if function:
            # insert on queue : first added to the last one
            self.setters_funcs.append(function)
        return self

    def getters(self, function=None, clear=False):
        """add a new getter function

        Keyword Arguments:
            function (function): a function that get a value and return a new one
            clear (bool): True - purge all previous functions

        Returns:
            Field: self
        """
        if clear:
            self.getters_funcs.clear()
        if function:
            # insert on top : last function added to the first one
            self.getters_funcs.insert(0, function)
        return self

    def mapping(self, mapping_name):
        """Set the mapping name

        Args:
            mapping_name (str): A mapping name for a specific field

        Returns:
            Field: self
        """
        self.mapping_name = mapping_name
        return self

    def list_of(self, inside_instanciator=None, instanciator=list):
        """Set as a list

        Keyword Arguments:
            inside_instanciator(class|function): a class or function that will instanciate an object
            instanciator(class|function): a custom assimilate list that support append() and iteration

        Returns:
            Field: self
        """
        self.instanciator = instanciator
        self.inside_instanciator = inside_instanciator
        self.is_list = True
        return self

    def hide(self):
        """Hide

        Returns:
            Field: self
        """
        self.hidden = True
        return self

    def unhide(self):
        """Un-hide

        Returns:
            Field: self
        """
        self.hidden = False
        return self

    def default(self, value):
        """Set the default value

        Args:
            value (object): a default value for the field

        Returns:
            Field: self
        """
        self.default_value = value
        return self

    def converter(self, loads=None, dumps=None):
        """Set converters for loaders and dumps()

        Keyword Arguments:
            loads (function): a load conversion function
            dumps (function): a dumps conversion function

        Returns:
            Field: self
        """
        if dumps is not None:
            self.dumps_converter = dumps
        if loads is not None:
            self.loads_converter = loads
        return self

    def match(self, name):
        """This field match a name

        Args:
            name (str): a name or mapping_name

        Returns:
            bool: True - match, False - Doesn't match
        """
        if self.name == name:
            return True
        if self.mapping_name and self.mapping_name == name:
            return True

        return False

    def get_instance(self, typing_instance):
        """Get the default value or new instance from instanciator

        Args:
            typing_instance (Typing2): The parent instance

        Returns:
            object: default value or new instance
        """
        if self.instanciator is None:
            return self.default_value

        if issubclass(self.instanciator, Typing2):
            return self.instanciator(parent=typing_instance)

        return self.instanciator()

    def get_inside_instance(self, data, typing_instance):
        """Get the default value or new instance from inside_instanciator

        For list content only

        Args:
            data (object): data to load passed to the instanciator
            typing_instance (Typing2): The parent instance

        Returns:
            object: default value or new instance
        """
        if self.inside_instanciator is None:
            return data

        if issubclass(self.inside_instanciator, Typing2):
            return self.inside_instanciator(data, parent=typing_instance)

        return self.inside_instanciator(data)

    def loads_convert(self, value):
        """Convert a value (loaders)

        Args:
            value (object): a value to convert

        Returns:
            object: a converted value
        """
        if self.loads_converter is None or value is None:
            return value

        return self.loads_converter(value)

    def dumps_convert(self, value):
        """Convert a value (dumps)

        Args:
            value (object): a value to convert

        Returns:
            object: a converted value
        """
        if self.dumps_converter is None or value is None:
            return value

        return self.dumps_converter(value)

class vField(Field):
    """vField is a virtual Field

    No real value is storable or readable.

    The purpose of vField is to provide a mechanism to get and set values
    from/for other variables.
    """
    def __get__(self, instance, owner):
        """Getter"""
        if instance is None:
            return self

        # Default value
        value = self.default_value

        # getters
        for func in self.getters_funcs:
            if (type(func).__name__ == "method"):
                # dynamic
                value = func(value)
            else:
                # static
                value = func(instance, value)

        return value

    def __set__(self, instance, value):
        """Setter

        Can convert value if loads converter is set.
        """
        value = self.loads_convert(value)

        for func in self.setters_funcs:
            if (type(func).__name__ == "method"):
                # dynamic
                value = func(value)
            else:
                # static
                value = func(instance, value)

    def __delete__(self, instance):
        pass

    def direct_get(self, instance):
        raise UnsupportedOperation("No real value can be get in a vField !")

    def direct_set(self, instance, value, bypass_converter=False):
        raise UnsupportedOperation("No real value can be set in a vField !")
