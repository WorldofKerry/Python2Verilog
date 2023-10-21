"""
Verilog Codegen
"""

import itertools
import logging
from typing import Optional

from python2verilog import ir
from python2verilog.backend.verilog import ast as ver
from python2verilog.backend.verilog.config import CodegenConfig, TestbenchConfig
from python2verilog.backend.verilog.fsm import FsmBuilder
from python2verilog.backend.verilog.module import Module
from python2verilog.backend.verilog.testbench import Testbench
from python2verilog.optimizer import backwards_replace
from python2verilog.utils.lines import Lines
from python2verilog.utils.typed import (
    guard,
    guard_dict,
    typed,
    typed_list,
    typed_strict,
)


class CodeGen:
    """
    Code Generator for Verilog
    """

    def __init__(
        self, root: ir.Node, context: ir.Context, config: Optional[CodegenConfig] = None
    ):
        """ "
        Builds tree from Graph IR
        """
        if not config:
            config = CodegenConfig()
        self.context = typed_strict(context, ir.Context)
        self.config = typed_strict(config, CodegenConfig)
        root_case = FsmBuilder(root, context, config).get_case()

        for item in root_case.case_items:
            self.context.add_state_weak(
                item.condition.to_string()
            )  # change to not weak

        assert isinstance(context.done_state, ir.State)
        self.context.add_state_weak(str(context.done_state))
        self.context.add_state_weak(str(context.idle_state))

        self._module = CodeGen.__new_module(root_case, self.context)

    @staticmethod
    def __new_module(root: ver.Case, context: ir.Context):
        """
        Creates a module wrapper from the context

        Requires context for I/O and declarations
        """
        return Module(context, root)

    @property
    def module(self):
        """
        Get Verilog module
        """
        assert isinstance(self._module, ver.Module)
        return self._module

    def get_module_lines(self):
        """
        Get Verilog module as Lines
        """
        return self.module.to_lines()

    def get_module_str(self):
        """
        Get Verilog module as string
        """
        return self.get_module_lines().to_string()

    def get_testbench(self, config: TestbenchConfig):
        """
        Creates testbench with multiple test cases

        Each element of self.context.test_cases represents a single test case

        :param random_ready: whether or not to have random ready signal in the while loop
        """
        logging.debug("%s", config)

        def make_display_stmt():
            """
            Creates a display statement for protocol signals and outputs

            $display("%0d, ...", ...);
            """
            string = '$display("%0d, %0d, '
            string += "%0d, " * (len(self.context.output_vars) - 1)
            string += '%0d", __ready, __valid'
            for var in self.context.output_vars:
                string += f", {var.ver_name}"
            string += ");"
            return ver.Statement(literal=string)

        assert isinstance(self.context, ir.Context)
        decl: list[ver.Declaration] = []
        decl.append(ver.Declaration("__clock", size=1, reg=True))
        decl.append(ver.Declaration("__start", size=1, reg=True))
        decl.append(ver.Declaration("__reset", size=1, reg=True))
        decl.append(ver.Declaration("__ready", size=1, reg=True))
        decl += [
            ver.Declaration(var.py_name, signed=True, reg=True)
            for var in self.context.input_vars
        ]
        decl.append(ver.Declaration("__done", size=1))
        decl.append(ver.Declaration("__valid", size=1))
        decl += [
            ver.Declaration(var.ver_name, signed=True)
            for var in self.context.output_vars
        ]

        ports = {decl.name: decl.name for decl in decl}
        assert guard_dict(ports, str, str)

        setups: list[ver.Statement] = list(decl)
        setups.append(ver.Instantiation(self.context.name, "DUT", ports))

        setups.append(ver.Statement(literal="always #5 __clock = !__clock;"))

        initial_body: list[ver.Statement | ver.While] = []
        initial_body.append(ver.BlockingSub(self.context.signals.clock, ir.UInt(0)))
        initial_body.append(ver.BlockingSub(self.context.signals.start, ir.UInt(0)))
        initial_body.append(ver.BlockingSub(self.context.signals.ready, ir.UInt(1)))
        initial_body.append(ver.BlockingSub(self.context.signals.reset, ir.UInt(1)))

        initial_body.append(ver.AtNegedgeStatement(self.context.signals.clock))
        initial_body.append(ver.BlockingSub(self.context.signals.reset, ir.UInt(0)))
        initial_body.append(ver.Statement())

        logging.debug("Making test cases")
        for i, test_case in enumerate(self.context.test_cases):
            # New test case and start
            initial_body.append(
                ver.Statement(
                    comment=f"============ Test Case {i} with "
                    f"arguments {str(test_case)} ============"
                )
            )
            for i, var in enumerate(self.context.input_vars):
                initial_body.append(
                    ver.BlockingSub(
                        ir.Var(py_name=var.py_name, ver_name=var.py_name),
                        ir.Int(int(test_case[i])),
                    )
                )
            initial_body.append(ver.BlockingSub(self.context.signals.start, ir.UInt(1)))

            # Post-start
            initial_body.append(ver.Statement())
            initial_body.append(ver.AtNegedgeStatement(self.context.signals.clock))
            for i, var in enumerate(self.context.input_vars):
                initial_body.append(
                    ver.BlockingSub(
                        ir.Var(py_name=var.py_name, ver_name=var.py_name),
                        ir.Unknown(),
                        comment="only need inputs when start is set",
                    )
                )
            initial_body.append(ver.BlockingSub(self.context.signals.start, ir.UInt(0)))
            initial_body.append(ver.Statement())

            # While loop
            while_body: list[ver.Statement] = []

            if self.context.is_generator:
                while_body.append(ver.AtPosedgeStatement(self.context.signals.clock))
                while_body.append(
                    ver.IfElse(
                        condition=self.context.signals.ready,
                        then_body=[make_display_stmt()],
                        else_body=[],
                    )
                )
                while_body.append(ver.AtNegedgeStatement(self.context.signals.clock))
                if config.random_ready:
                    while_body.append(
                        ver.Statement("__ready = $urandom_range(0, 4) === 0;")
                    )

                initial_body.append(
                    ver.While(
                        condition=ir.UBinOp(
                            ir.UnaryOp("!", self.context.signals.done),
                            "||",
                            ir.UnaryOp("!", self.context.signals.ready),
                        ),
                        body=while_body,
                    )
                )
                initial_body.append(ver.Statement())

            else:
                while_body.append(ver.AtNegedgeStatement(self.context.signals.clock))
                if config.random_ready:
                    while_body.append(
                        ver.Statement("__ready = $urandom_range(0, 4) === 0;")
                    )
                initial_body.append(
                    ver.While(
                        condition=ir.UBinOp(
                            ir.UnaryOp("!", self.context.signals.done),
                            "||",
                            ir.UnaryOp("!", self.context.signals.ready),
                        ),
                        body=while_body,
                    )
                )
                initial_body.append(
                    ver.IfElse(
                        condition=self.context.signals.ready,
                        then_body=[make_display_stmt()],
                        else_body=[],
                    )
                )

        initial_body.append(ver.Statement(literal="$finish;"))

        initial_loop = ver.Initial(body=initial_body)

        logging.debug("Creating python test code")
        python_test_code = Lines()
        for case in self.context.test_cases:
            python_test_code += f"print(list({self.context.name}(*{case})))"
        if self.context:
            module = ver.Module(
                self.context.testbench_name,
                [],
                [],
                body=setups + [initial_loop],
                is_not_testbench=False,
                header=Lines(
                    f"/*\n\n# Python Function\n{self.context.py_string}\n\n"
                    f"# Test Cases\n{python_test_code}\n*/\n\n"
                ),
            )
            return module
        raise RuntimeError("Needs the context")

    def get_testbench_lines(self, config: TestbenchConfig):
        """
        New Testbench as lines
        """
        return self.get_testbench(config=config).to_lines()

    def get_testbench_str(self, config: TestbenchConfig):
        """
        New testbench as str
        """
        return self.get_testbench_lines(config=config).to_string()
