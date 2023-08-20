"""Context for Intermediate Representation"""
from __future__ import annotations
import ast
import copy
from dataclasses import dataclass, field
import io
from types import FunctionType
from typing import Optional, IO
import warnings

from python2verilog.utils.generics import GenericReprAndStr
from ..utils.assertions import assert_list_type, assert_type, assert_dict_type
from ..ir import Var


@dataclass
class Context(GenericReprAndStr):
    """
    Context needed by the Intermediate Representation
    E.g. variables, I/O, parameters, localparam
    """

    # pylint: disable=too-many-instance-attributes
    name: str = ""
    test_cases: list[int | list] = field(default_factory=list)

    py_func: Optional[FunctionType] = None
    py_ast: Optional[ast.FunctionDef] = None

    input_types: list = field(default_factory=list)
    output_types: list = field(default_factory=list)

    optimization_level: int = 1

    write: bool = False
    overwrite: bool = False
    module_file: IO = io.StringIO()
    testbench_file: IO = io.StringIO()

    _global_vars: list[Var] = field(default_factory=list)
    _input_vars: list[Var] = field(default_factory=list)
    _output_vars: list[Var] = field(default_factory=list)
    _states: set[str] = field(default_factory=set)

    valid_signal: Var = Var("valid")
    ready_signal: Var = Var("ready")
    clock_signal: Var = Var("clock")
    start_signal: Var = Var("start")
    reset_signal: Var = Var("reset")

    state_var: Var = Var("state")

    entry_state: str = "UNSPECIFIED ENTRY"
    ready_state: str = "UNSPECIFIED STATE"

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
    def states(self):
        """
        State variables
        """
        return copy.deepcopy(self._states)

    def is_declared(self, name: str):
        """
        Checks if a Python variable has been already declared or not
        """

        def get_strs(variables: list[Var]):
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

    def __check_types(self, expected_types: list, actual_values: list):
        for expected, actual in zip(expected_types, actual_values):
            assert isinstance(
                actual, expected
            ), f"Expected {expected}, got {type(actual)}, with value {actual}, \
                with function name {self.name}"

    def check_input_types(self, input_):
        """
        Checks if input to functions' types matches previous inputs
        """
        self.__check_types(self.input_types, input_)

    def check_output_types(self, output):
        """
        Checks if outputs to functions' types matches previous outputs
        """
        self.__check_types(self.output_types, output)
