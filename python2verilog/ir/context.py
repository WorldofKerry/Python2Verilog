"""Context for Intermediate Representation"""
from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Optional
from ..utils.assertions import assert_list_type, assert_type, assert_dict_type


@dataclass
class Context:
    """
    Context needed by the Intermediate Representation
    E.g. variables, I/O, parameters, localparam
    """

    name: str = ""
    global_vars: dict[str, str] = field(default_factory=dict)
    input_vars: list[str] = field(default_factory=list)
    output_vars: list[str] = field(default_factory=list)
    _state_vars: set[str] = field(default_factory=set)
    entry: str = ""
    exit: str = ""

    @property
    def state_vars(self):
        """
        State vars
        """
        return copy.deepcopy(self._state_vars)

    def is_declared(self, name: str):
        """
        Checks if a variable has been already declared or not
        """
        return name in set([*self.global_vars, *self.input_vars, *self.output_vars])

    def to_string(self):
        """
        To string
        """
        return str(self.__dict__)

    def add_state(self, name: str):
        """
        Add a state, making sure no pre-existing state what that name exists
        """
        if name in self._state_vars:
            raise RuntimeError(f"Attempting to add {name} when it already exists")
        self.add_state_weak(name)

    def add_state_weak(self, name: str):
        """
        Add a state
        """
        assert isinstance(name, str)
        self._state_vars.add(name)
