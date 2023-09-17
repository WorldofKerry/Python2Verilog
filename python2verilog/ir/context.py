"""
The context of a generator

Includes the function, its representation and its usage information
"""
from __future__ import annotations

import ast
import copy
import io
from dataclasses import dataclass, field
from types import FunctionType
from typing import Any, Optional

from python2verilog.api.modes import Modes
from python2verilog.ir.expressions import State, Var
from python2verilog.ir.graph import DoneNode
from python2verilog.ir.instance import Instance
from python2verilog.ir.signals import ProtocolSignals
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
    testbench_suffix: str = "_tb"

    test_cases: list[tuple[int]] = field(default_factory=list)

    py_func: Optional[FunctionType] = None
    py_string: Optional[str] = None
    _py_ast: Optional[ast.FunctionDef] = None

    input_types: list[type[Any]] = field(default_factory=list)
    output_types: list[type[Any]] = field(default_factory=list)

    optimization_level: int = -1

    mode: Modes = Modes.NO_WRITE

    _global_vars: list[Var] = field(default_factory=list)
    _input_vars: list[Var] = field(default_factory=list)
    _output_vars: list[Var] = field(default_factory=list)
    _states: set[str] = field(default_factory=set)

    signals: ProtocolSignals = ProtocolSignals(
        start_signal=Var("start"),
        done_signal=Var("done"),
        ready_signal=Var("ready"),
        valid_signal=Var("valid"),
    )

    state_var: Var = Var("state")

    _done_state: State = State("_state_done")
    _entry_state: Optional[str] = None

    # Function calls
    namespace: dict[str, Context] = field(default_factory=dict)  # callable functions
    instances: dict[str, Instance] = field(default_factory=dict)  # generator instances

    def _repr(self):
        """
        Avoids recursion on itself
        """
        dic = self.__dict__
        del dic["namespace"]
        return dic

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

        assert check_list(self.input_types), "Input types not inferred"
        assert check_list(self.input_vars), self

        assert check_list(self.output_types), self
        assert check_list(self.output_vars), self

        assert isinstance(self.optimization_level, int), self
        assert self.optimization_level >= 0, f"{self.optimization_level} {self.name}"

        if self._entry_state:
            assert self.entry_state in self.states, self

        for value in self.signals.values():
            assert get_typed(value, Var)

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
        assert isinstance(self._module_file, io.IOBase), type(self._module_file)
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
    def done_state(self):
        """
        The ready state
        """
        assert isinstance(self._done_state, State), self
        return self._done_state

    @done_state.setter
    def done_state(self, other: State):
        assert isinstance(other, State)
        self._done_state = other

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
        var = get_typed(var, Var)
        if (
            var in self._global_vars
            or var in self._input_vars
            or var in self.output_vars
        ):
            return
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
        assert len(expected_types) == len(actual_values)
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

    def create_instance(self, name: str) -> Instance:
        """
        Create generator instance
        """
        inst_input_vars = list(
            map(lambda var: Var(f"{name}_{self.name}_{var.py_name}"), self.input_vars)
        )
        inst_output_vars = list(
            map(lambda var: Var(f"{name}_{self.name}_{var.py_name}"), self.output_vars)
        )
        args = {
            key: Var(f"{name}_{self.name}__{value.py_name}")
            for key, value in self.signals.instance_specific()
        }

        signals = ProtocolSignals(**args)

        return Instance(
            self.name,
            Var(name),
            inst_input_vars,
            inst_output_vars,
            signals,
        )
