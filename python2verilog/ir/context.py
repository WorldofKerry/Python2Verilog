"""Context for Intermediate Representation"""
from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Optional
import warnings
from ..utils.assertions import assert_list_type, assert_type, assert_dict_type
from ..ir import InputVar


@dataclass
class Context:
    """
    Context needed by the Intermediate Representation
    E.g. variables, I/O, parameters, localparam
    """

    # pylint: disable=too-many-instance-attributes
    name: str = ""
    _global_vars: list[InputVar] = field(default_factory=list)
    _input_vars: list[InputVar] = field(default_factory=list)
    _output_vars: list[InputVar] = field(default_factory=list)
    _states: set[str] = field(default_factory=set)

    valid_signal: InputVar = InputVar("valid")
    ready_signal: InputVar = InputVar("ready")
    clock_signal: InputVar = InputVar("clock")
    start_signal: InputVar = InputVar("start")
    reset_signal: InputVar = InputVar("reset")

    state_var: InputVar = InputVar("state")
    entry: str = ""
    ready_state: str = ""

    @property
    def input_vars(self):
        """
        Input variables
        """
        return copy.deepcopy(self._input_vars)

    @input_vars.setter
    def input_vars(self, other: list[InputVar]):
        self._input_vars = assert_list_type(other, InputVar)

    @property
    def output_vars(self):
        """
        Output variables
        """
        return tuple(self._output_vars)

    @output_vars.setter
    def output_vars(self, other: list[InputVar]):
        self._output_vars = assert_list_type(other, InputVar)

    @property
    def global_vars(self):
        """
        Global variables
        """
        return tuple(self._global_vars)

    @global_vars.setter
    def global_vars(self, other: list[InputVar]):
        self._global_vars = assert_list_type(other, InputVar)

    def add_global_var(self, var: InputVar):
        """
        Appends global var
        """
        self._global_vars.append(assert_type(var, InputVar))

    @property
    def states(self):
        """
        State variables
        """
        return copy.deepcopy(self._states)

    def is_declared(self, name: str):
        """
        Checks if a Python variable has been already declared or not
        """

        def get_strs(variables: list[InputVar]):
            """
            Maps vars to str
            """
            for var in variables:
                yield var.py_name

        assert isinstance(name, str)
        variables = [
            *list(get_strs(self._global_vars)),
            *list(get_strs(self._input_vars)),
            *list(get_strs(self._output_vars)),
        ]
        return name in variables

    def to_string(self):
        """
        To string
        """
        return str(self.__dict__)

    def add_state(self, name: str):
        """
        Add a state, making sure no pre-existing state what that name exists
        """
        if name in self._states:
            raise RuntimeError(f"Attempting to add {name} when it already exists")
        self.add_state_weak(name)

    def add_state_weak(self, name: str):
        """
        Add a state
        """
        assert isinstance(name, str)
        self._states.add(name)
