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
    global_vars: dict[str, str] = field(default_factory=dict)
    input_vars: list[str] = field(default_factory=list)
    output_vars: list[str] = field(default_factory=list)
    state_vars: list[str] = field(default_factory=list)

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
