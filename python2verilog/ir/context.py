"""Context for Intermediate Representation"""
from __future__ import annotations
from typing import Optional
from ..utils.assertions import assert_list_type, assert_type, assert_dict_type


class Context:
    """
    Context needed by the Intermediate Representation
    E.g. variables, I/O, parameters, localparam
    """

    def __init__(
        self,
        name: str = "",
        global_vars: Optional[dict[str, str]] = None,
        input_vars: Optional[list[str]] = None,
        output_vars: Optional[list[str]] = None,
        state_vars: Optional[list[str]] = None,
    ):
        self.name = assert_type(name, str)
        self.global_vars = assert_dict_type(global_vars, str, str)
        self.input_vars = assert_list_type(input_vars, str)
        self.output_vars = assert_list_type(output_vars, str)
        self.state_vars = assert_list_type(state_vars, str)

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
