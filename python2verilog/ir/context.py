"""Context for Intermediate Representation"""
from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Optional
import warnings
from ..utils.assertions import assert_list_type, assert_type, assert_dict_type
from ..ir import Var


@dataclass
class Context:
    """
    Context needed by the Intermediate Representation
    E.g. variables, I/O, parameters, localparam
    """

    name: str = ""
    _global_vars: list[Var] = field(default_factory=list)
    _input_vars: list[Var] = field(default_factory=list)
    _output_vars: list[Var] = field(default_factory=list)
    _states: set[str] = field(default_factory=set)
    entry: str = ""
    ready: str = ""

    @property
    def input_vars(self):
        """
        Input variables
        """
        return copy.deepcopy(self._input_vars)

    @input_vars.setter
    def input_vars(self, other: list[Var]):
        self._input_vars = assert_list_type(other, Var)

    @property
    def output_vars(self):
        """
        Output variables
        """
        return tuple(self._output_vars)

    @output_vars.setter
    def output_vars(self, other: list[Var]):
        self._output_vars = assert_list_type(other, Var)

    @property
    def global_vars(self):
        """
        Global variables
        """
        return tuple(self._global_vars)

    @global_vars.setter
    def global_vars(self, other: list[Var]):
        self._global_vars = assert_list_type(other, Var)

    def add_global_var(self, var: Var):
        """
        Appends global var
        """
        self._global_vars.append(assert_type(var, Var))

    @property
    def state_vars(self):
        """
        State variables
        """
        return copy.deepcopy(self._states)

    def is_declared(self, name: str):
        """
        Checks if a Python variable has been already declared or not
        """

        def get_strs(vars: list[Var]):
            """
            Maps vars to str
            """
            for var in vars:
                yield (var.py_name)

        assert isinstance(name, str)
        vars = [
            *list(get_strs(self._global_vars)),
            *list(get_strs(self._input_vars)),
            *list(get_strs(self._output_vars)),
        ]
        warnings.warn(str(vars))
        return name in vars

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
