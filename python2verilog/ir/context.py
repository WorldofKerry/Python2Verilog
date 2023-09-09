"""Context for Intermediate Representation"""
from __future__ import annotations

import ast
import copy
import io
from dataclasses import dataclass, field
from types import FunctionType
from typing import Any, Optional

from python2verilog.ir.expressions import Var
from python2verilog.utils.assertions import assert_typed_dict, get_typed, get_typed_list
from python2verilog.utils.env_vars import is_debug_mode
from python2verilog.utils.generics import GenericReprAndStr

DEFAULT_STATE_NAME = "___PYTHON_2_VERILOG_STATE___"


@dataclass
class Context(GenericReprAndStr):
    """
    Context needed by the Intermediate Representation
    E.g. variables, I/O, parameters, localparam
    """

    # pylint: disable=too-many-instance-attributes
    name: str = ""
    test_cases: list[tuple[int]] = field(default_factory=list)

    py_func: Optional[FunctionType] = None
    py_string: Optional[str] = None
    _py_ast: Optional[ast.FunctionDef] = None

    input_types: list[type[Any]] = field(default_factory=list)
    output_types: list[type[Any]] = field(default_factory=list)

    optimization_level: int = -1

    write: bool = False
    _module_file: Optional[io.IOBase] = None
    _testbench_file: Optional[io.IOBase] = None

    _global_vars: list[Var] = field(default_factory=list)
    _input_vars: list[Var] = field(default_factory=list)
    _output_vars: list[Var] = field(default_factory=list)
    _states: set[str] = field(default_factory=set)

    valid_signal: Var = Var("valid")
    done_signal: Var = Var("done")
    clock_signal: Var = Var("clock")
    start_signal: Var = Var("start")
    reset_signal: Var = Var("reset")
    ready_signal: Var = Var("ready")

    state_var: Var = Var("state")

    _entry_state: Optional[str] = None
    _ready_state: Optional[str] = None

    def __del__(self):
        if self._module_file:
            self._module_file.close()
        if self._testbench_file:
            self._testbench_file.close()

    def validate(self):
        """
        Validates that all fields of context are populated.

        Checks invariants.

        Only does checks in debug mode.

        :return: self
        """
        if not is_debug_mode():
            return self

        assert isinstance(self.py_ast, ast.FunctionDef), self
        assert isinstance(self.py_func, FunctionType), self

        def check_list(list_: list):
            return isinstance(list_, list) and len(list_) > 0

        assert check_list(self.input_types), self
        assert check_list(self.input_vars), self

        assert check_list(self.output_types), self
        assert check_list(self.output_vars), self

        assert isinstance(self.optimization_level, int), self
        assert self.optimization_level >= 0

        if self.write:
            if self._module_file:
                assert isinstance(self.module_file, io.IOBase), self
            if self._testbench_file:
                assert isinstance(self.testbench_file, io.IOBase), self

        if self._entry_state:
            assert self.entry_state in self.states, self
        if self._ready_state:
            assert self.ready_state in self.states, self

        assert get_typed(self.ready_signal, Var)
        assert get_typed(self.clock_signal, Var)
        assert get_typed(self.done_signal, Var)
        assert get_typed(self.valid_signal, Var)
        assert get_typed(self.reset_signal, Var)
        assert get_typed(self.start_signal, Var)

        return self

    @property
    def py_ast(self):
        """
        Python ast node rooted at function
        """
        assert isinstance(self._py_ast, ast.FunctionDef)
        return self._py_ast

    @py_ast.setter
    def py_ast(self, other: ast.FunctionDef):
        assert isinstance(other, ast.FunctionDef)
        self._py_ast = other

    @property
    def testbench_file(self):
        """
        Testbench stream
        """
        assert isinstance(self._testbench_file, io.IOBase)
        return self._testbench_file

    @testbench_file.setter
    def testbench_file(self, other: io.IOBase):
        assert isinstance(other, io.IOBase)
        self._testbench_file = other

    @property
    def module_file(self):
        """
        Module stream
        """
        assert isinstance(self._module_file, io.IOBase)
        return self._module_file

    @module_file.setter
    def module_file(self, other: io.IOBase):
        assert isinstance(other, io.IOBase)
        self._module_file = other

    @property
    def entry_state(self):
        """
        The first state that does work in the graph representation
        """
        assert isinstance(self._entry_state, str), self
        return self._entry_state

    @entry_state.setter
    def entry_state(self, other: str):
        assert isinstance(other, str)
        self._entry_state = other

    @property
    def ready_state(self):
        """
        The ready state
        """
        assert isinstance(self._ready_state, str), self
        return self._ready_state

    @ready_state.setter
    def ready_state(self, other: str):
        assert isinstance(other, str)
        self._ready_state = other

    @property
    def input_vars(self):
        """
        Input variables
        """
        return copy.deepcopy(self._input_vars)

    @input_vars.setter
    def input_vars(self, other: list[Var]):
        self._input_vars = get_typed_list(other, Var)

    @property
    def output_vars(self):
        """
        Output variables
        """
        return copy.deepcopy(self._output_vars)

    @output_vars.setter
    def output_vars(self, other: list[Var]):
        self._output_vars = get_typed_list(other, Var)

    def default_output_vars(self):
        """
        Sets own output vars to default based on number of output variables
        """
        assert self.output_types and len(self.output_types) > 0
        self._output_vars = [Var(str(i)) for i in range(len(self.output_types))]

    @property
    def global_vars(self):
        """
        Global variables
        """
        return tuple(self._global_vars)

    @global_vars.setter
    def global_vars(self, other: list[Var]):
        self._global_vars = get_typed_list(other, Var)

    def add_global_var(self, var: Var):
        """
        Appends global var
        """
        self._global_vars.append(get_typed(var, Var))

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

    def __check_types(
        self, expected_types: list[type[Any]], actual_values: list[type[Any]]
    ):
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
