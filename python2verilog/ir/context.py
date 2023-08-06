"""Context for Intermediate Representation"""
from __future__ import annotations
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
    _global_vars: dict[str, str] = field(default_factory=dict)
    input_vars: list[str] = field(default_factory=list)
    output_vars: list[str] = field(default_factory=list)
    _state_vars: set[str] = field(default_factory=set)
    entry: str = ""
    exit: str = ""

    @property
    def global_vars(self):
        # if "_statelmaodone" in self._global_vars:
        #     raise Exception()
        return self._global_vars

    @global_vars.setter
    def global_vars(self, other):
        self._global_vars = other

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
        Add a state
        """
        assert isinstance(name, str)
        # print(f"{self._state_vars}")
        if name in self._state_vars:
            raise RuntimeError(f"Attempting to add {name} when it already exists")
        self._state_vars.add(name)
