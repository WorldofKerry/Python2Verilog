"""
The context of a generator

Includes the function, its representation and its usage information
"""
from __future__ import annotations

import ast
import copy
import io
import logging
from dataclasses import dataclass, field
from types import FunctionType
from typing import Any, Optional, Sequence, Union

from python2verilog.api.modes import Modes
from python2verilog.ir.expressions import ExclusiveVar, State, Var
from python2verilog.ir.graph import DoneNode
from python2verilog.ir.instance import Instance
from python2verilog.ir.signals import ProtocolSignals
from python2verilog.utils.env import is_debug_mode
from python2verilog.utils.generics import GenericReprAndStr
from python2verilog.utils.typed import (
    guard,
    guard_dict,
    typed,
    typed_list,
    typed_strict,
)


@dataclass
class Context(GenericReprAndStr):
    """
    Context needed by the Intermediate Representation
    E.g. variables, I/O, parameters, localparam
    """

    # pylint: disable=too-many-instance-attributes
    name: str = ""
    testbench_suffix: str = "_tb"

    test_cases: list[tuple[int, ...]] = field(default_factory=list)

    py_func: Optional[FunctionType] = None
    py_string: Optional[str] = None
    _py_ast: Optional[ast.FunctionDef] = None

    input_types: Optional[list[type[Any]]] = None
    output_types: Optional[list[type[Any]]] = None

    optimization_level: int = -1

    mode: Modes = Modes.NO_WRITE

    _global_vars: list[Var] = field(default_factory=list)
    _input_vars: Optional[list[Var]] = None
    _output_vars: Optional[list[ExclusiveVar]] = None
    _states: set[str] = field(default_factory=set)

    signals: ProtocolSignals = ProtocolSignals(
        start=Var("start"),
        done=Var("done"),
        ready=Var("ready"),
        valid=Var("valid"),
    )

    state_var: Var = Var("state")

    _done_state: State = State("_state_done")
    idle_state: State = State("_state_idle")
    _entry_state: Optional[State] = None

    # Function calls
    namespace: dict[str, Context] = field(default_factory=dict)  # callable functions
    instances: dict[str, Instance] = field(default_factory=dict)  # generator instances

    @classmethod
    def empty_valid(cls):
        """
        Creates an empty but valid context for testing purposes
        """
        cxt = cls()
        cxt.input_types = []
        cxt.input_vars = []
        cxt.output_types = []
        cxt.output_vars = []
        return cxt

    @property
    def testbench_name(self) -> str:
        """
        Returns test bench module name in the generated verilog
        """
        return f"{self.name}{self.testbench_suffix}"

    def _repr(self):
        """
        Avoids recursion on itself
        """
        dic = copy.deepcopy(self.__dict__)
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

        def check_list(list_: Union[list[Any], None]):
            return isinstance(list_, list)

        if not check_list(self.input_types):

            def input_mapper(arg: ast.arg) -> type[Any]:
                """
                Maps a string annotation id to type
                """
                assert arg.annotation, f"{ast.dump(arg)}"
                assert isinstance(arg.annotation, ast.Name)
                if arg.annotation.id == "int":
                    return type(0)
                raise TypeError(f"{ast.dump(arg)}")

            logging.info("Using type hints of %s for input types", self.name)
            input_args: list[ast.arg] = self.py_ast.args.args
            assert isinstance(input_args, list), f"{ast.dump(self.py_ast)}"
            self.input_types = list(map(input_mapper, input_args))
        assert check_list(self.input_types), self
        assert check_list(self.input_vars), self

        if not check_list(self.output_types):

            def output_mapper(arg: ast.Name) -> type[Any]:
                """
                Maps a string annotation id to type
                """
                if arg.id == "int":
                    return type(0)
                raise TypeError(f"{ast.dump(arg)}")

            logging.info("Using type hints of %s for return types", self.name)
            output_args: list[ast.arg]
            if isinstance(self.py_ast.returns, ast.Subscript):
                assert isinstance(self.py_ast.returns.slice, ast.Tuple)
                output_args = self.py_ast.returns.slice.elts
            else:
                output_args = [self.py_ast.returns]
            assert isinstance(output_args, list), f"{ast.dump(self.py_ast)}"
            self.output_types = list(map(output_mapper, output_args))
            self.default_output_vars()

        assert check_list(self.output_types), self
        assert check_list(self.output_vars), self
        assert isinstance(self._output_vars, list)

        assert isinstance(self.optimization_level, int), self
        assert self.optimization_level >= 0, f"{self.optimization_level} {self.name}"

        if self._entry_state:
            assert str(self.entry_state) in self.states, self

        for value in self.signals.values():
            assert typed(value, Var)

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
        assert isinstance(self._entry_state, State), self
        return self._entry_state

    @entry_state.setter
    def entry_state(self, other: State):
        assert isinstance(other, State)
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
        assert guard(self._input_vars, list)
        return copy.deepcopy(self._input_vars)

    @input_vars.setter
    def input_vars(self, other: list[Var]):
        self._input_vars = typed_list(other, Var)

    @property
    def output_vars(self):
        """
        Output variables
        """
        assert guard(self._output_vars, list), f"Unknown output variables {self}"
        return copy.deepcopy(self._output_vars)

    @output_vars.setter
    def output_vars(self, other: list[ExclusiveVar]):
        self._output_vars = typed_list(other, ExclusiveVar)

    def default_output_vars(self):
        """
        Sets own output vars to default based on number of output variables
        """
        assert self.output_types and len(self.output_types) > 0
        self._output_vars = [
            ExclusiveVar(f"out{i}") for i in range(len(self.output_types))
        ]

    @property
    def global_vars(self):
        """
        Global variables
        """
        return tuple(self._global_vars)

    @global_vars.setter
    def global_vars(self, other: list[Var]):
        self._global_vars = typed_list(other, Var)

    def add_global_var(self, var: Var):
        """
        Appends global var
        """
        var = typed_strict(var, Var)
        if (
            var in self._global_vars
            or var in self.input_vars
            or var in self.output_vars
        ):
            return
        self._global_vars.append(typed_strict(var, Var))

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

        def get_strs(variables: Sequence[Var]):
            """
            Maps vars to str
            """
            for var in variables:
                yield var.py_name

        assert isinstance(name, str)
        variables = [
            *list(get_strs(self.global_vars)),
            *list(get_strs(self.input_vars)),
            *list(get_strs(self.output_vars)),
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
        assert guard(self.input_types, list)
        self.__check_types(self.input_types, input_)

    def check_output_types(self, output):
        """
        Checks if outputs to functions' types matches previous outputs
        """
        assert guard(self.output_types, list)
        self.__check_types(self.output_types, output)

    def create_instance(self, name: str) -> Instance:
        """
        Create generator instance
        """
        self.validate()
        inst_input_vars: list[Var] = list(
            map(
                lambda var: ExclusiveVar(f"{name}_{self.name}_{var.py_name}"),
                self.input_vars,
            )
        )
        inst_output_vars: list[Var] = list(
            map(
                lambda var: ExclusiveVar(f"{name}_{self.name}_{var.py_name}"),
                self.output_vars,
            )
        )
        args: dict[str, Var] = {
            key: ExclusiveVar(f"{name}_{self.name}__{value.py_name}")
            for key, value in self.signals.instance_specific_items()
        }

        signals = ProtocolSignals(**args)

        return Instance(
            self.name,
            Var(name),
            inst_input_vars,
            inst_output_vars,
            signals,
        )
