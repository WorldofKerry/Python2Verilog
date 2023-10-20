"""
Verilog Codegen
"""

import itertools
import logging
from typing import Iterator, Optional, cast

from python2verilog import ir
from python2verilog.backend.verilog import ast as ver
from python2verilog.backend.verilog.config import CodegenConfig, TestbenchConfig
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
        root_case = CaseBuilder(root, context, config).get_case()

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
        assert isinstance(root, ver.Case)
        assert isinstance(context, ir.Context)

        inputs = []
        for var in context.input_vars:
            inputs.append(var.py_name)

        outputs = []
        for var in context.output_vars:
            outputs.append(var.ver_name)

        def make_debug_display(context: ir.Context):
            """
            Creates a display statement for all signals

            $display("%0d, ...", ...);
            """
            vars_: list[str] = []
            vars_ += map(
                lambda x: x.ver_name, context.signals.instance_specific_values()
            )
            vars_ += map(lambda x: x.py_name, context.input_vars)
            vars_ += map(lambda x: x.ver_name, context.input_vars)
            vars_ += map(lambda x: x.ver_name, context.output_vars)
            vars_ += map(lambda x: x.ver_name, context.local_vars)
            str_ = f'$display("{context.name},%s,'
            str_ += "=%0d,".join(vars_) + '=%0d", '
            str_ += f"{context.state_var.ver_name}.name, "
            str_ += ", ".join(vars_)
            str_ += ");"
            return str_

        def create_instance_zeroed_signals() -> Iterator[ver.Statement]:
            """
            Instance signals that should always be set to zero be default
            """
            for instance in context.generator_instances.values():
                yield ver.NonBlockingSubsitution(instance.signals.ready, ir.UInt(0))
                yield ver.NonBlockingSubsitution(instance.signals.start, ir.UInt(0))

        always = ver.PosedgeSyncAlways(
            context.signals.clock,
            body=[
                ver.Statement("`ifdef DEBUG"),
                ver.Statement(make_debug_display(context)),
                ver.Statement("`endif"),
                ver.Statement(),
            ]
            + list(create_instance_zeroed_signals())
            + [
                ver.Statement(),
                ver.IfElse(
                    context.signals.ready,
                    cast(
                        list[ver.Statement],
                        [
                            ver.NonBlockingSubsitution(
                                context.signals.valid, ir.UInt(0)
                            ),
                            ver.NonBlockingSubsitution(
                                context.signals.done, ir.UInt(0)
                            ),
                        ],
                    ),
                    [],
                ),
            ]
            + [
                ver.Statement(),
                ver.Statement(comment="Start signal takes precedence over reset"),
                ver.IfElse(
                    ir.UBinOp(context.signals.reset, "||", context.signals.start),
                    then_body=[
                        ver.NonBlockingSubsitution(
                            context.state_var,
                            context.idle_state,
                        ),
                        ver.NonBlockingSubsitution(
                            context.signals.done,
                            ir.UInt(0),
                        ),
                        ver.NonBlockingSubsitution(
                            context.signals.valid,
                            ir.UInt(0),
                        ),
                    ],
                    else_body=[],
                ),
                ver.Statement(),
            ]
            + CodeGen.__make_start_if_else(root, context),
        )
        body: list[ver.Statement] = []

        body += [
            ver.Statement(comment="Local variables"),
        ]
        context.local_vars.sort(key=lambda x: x.ver_name)
        body += [
            ver.Declaration(v.ver_name, reg=True, signed=True)
            for v in context.local_vars
        ]

        body += [
            ver.Declaration(var.ver_name, reg=True, signed=True)
            for var in context.input_vars
        ]

        for instance in context.generator_instances.values():
            body.append(
                ver.Statement(
                    comment="================ Function Instance ================"
                )
            )
            module = context.namespace[instance.module_name]
            defaults = {
                module.signals.valid: instance.signals.valid,
                module.signals.done: instance.signals.done,
                module.signals.clock: context.signals.clock,
                module.signals.start: instance.signals.start,
                module.signals.reset: instance.signals.reset,
                module.signals.ready: instance.signals.ready,
            }
            # defaults = dict(zip(module.signals.values(), instance.signals.values()))
            for var in instance.inputs:
                body.append(ver.Declaration(name=var.ver_name, reg=True))
            for var in instance.outputs:
                body.append(ver.Declaration(name=var.ver_name))
            body.append(ver.Declaration(name=instance.signals.valid.ver_name, size=1))
            body.append(ver.Declaration(name=instance.signals.done.ver_name, size=1))
            body.append(
                ver.Declaration(name=instance.signals.start.ver_name, size=1, reg=True)
            )
            body.append(
                ver.Declaration(name=instance.signals.ready.ver_name, size=1, reg=True)
            )
            body.append(
                ver.Instantiation(
                    instance.module_name,
                    instance.var.ver_name,
                    {
                        key.py_name: value.ver_name
                        for key, value in zip(
                            module.input_vars,
                            instance.inputs,
                        )
                    }
                    | {
                        key.ver_name: value.ver_name
                        for key, value in zip(
                            module.output_vars,
                            instance.outputs,
                        )
                    }
                    | {key.ver_name: value.ver_name for key, value in defaults.items()},
                )
            )

        body.append(ver.Statement(comment="Core"))
        body.append(always)

        state_vars = {
            key: ir.UInt(index) for index, key in enumerate(sorted(context.states))
        }

        return ver.Module(
            name=context.name,
            inputs=inputs,
            outputs=outputs,
            body=body,
            localparams=state_vars,
        )

    @staticmethod
    def __make_start_if_else(
        root: ver.Case, context: ir.Context
    ) -> list[ver.Statement]:
        """
        if (_start) begin
            ...
        end else begin
            ...
        end
        """
        then_body: list[ver.Statement] = []
        for var in context.input_vars:
            then_body.append(
                ver.NonBlockingSubsitution(
                    ir.Var(py_name=var.ver_name, ver_name=var.ver_name),
                    ir.Expression(var.py_name),
                )
            )

        if context.optimization_level > 0:
            # Optimization to include the entry state in the start ifelse

            # Map cached inputs to input signals (cached inputs not updated yet)
            mapping = {
                ir.Var(py_name=var.ver_name, ver_name=var.ver_name): ir.Expression(
                    var.py_name
                )
                for var in context.input_vars
            }

            # Get statements in entry state
            stmt_stack: list[ver.Statement] = []
            for item in root.case_items:
                if item.condition == context.entry_state:
                    stmt_stack += item.statements
                    then_body += item.statements
                    root.case_items.remove(item)
                    break

            # Replace usage of cached inputs with input signals
            while stmt_stack:
                stmt = stmt_stack.pop()
                if isinstance(stmt, ver.NonBlockingSubsitution):
                    stmt.rvalue = backwards_replace(stmt.rvalue, mapping)
                elif isinstance(stmt, ver.IfElse):
                    stmt.condition = backwards_replace(stmt.condition, mapping)
                    stmt_stack += stmt.then_body
                    stmt_stack += stmt.else_body
                else:
                    raise TypeError(f"Unexpected {type(stmt)} {stmt}")
        else:
            then_body.append(
                ver.NonBlockingSubsitution(context.state_var, context.entry_state)
            )

        if_else = ver.IfElse(
            context.signals.start,
            then_body,
            [
                ver.Statement(
                    comment="If ready or not valid, then continue computation"
                ),
                ver.IfElse(
                    ir.UBinOp(
                        context.signals.ready,
                        "||",
                        ir.UnaryOp("!", context.signals.valid),
                    ),
                    [root],
                    [],
                ),
            ],
        )
        return [if_else]

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


class CaseBuilder:
    """
    Creates a case statement for the IR Graph
    """

    def __init__(
        self, root: ir.Node, context: ir.Context, config: Optional[CodegenConfig] = None
    ):
        # Member Vars
        if not config:
            config = CodegenConfig()
        self.visited: set[str] = set()
        self.context = context
        self.case = ver.Case(expression=context.state_var, case_items=[])
        self.root = typed_strict(root, ir.Node)
        self.config = typed_strict(config, CodegenConfig)

        # Member Funcs
        instance = itertools.count()
        self.next_unique = lambda: next(instance)

    def get_case(self) -> ver.Case:
        """
        Gets case statement/block
        """
        # Start recursion and create FSM
        self.case.case_items.append(self.new_caseitem(self.root))

        # Reverse states for readability (states are built backwards)
        self.case.case_items = list(reversed(self.case.case_items))

        return self.case

    @staticmethod
    def create_quick_done(context: ir.Context) -> ver.IfElse:
        """
        if ready:
            done = 1
            state = idle
        else:
            state = done
        """
        return ver.IfElse(
            condition=ir.UBinOp(
                ir.UnaryOp("!", context.signals.valid), "&&", context.signals.ready
            ),
            then_body=[
                ver.NonBlockingSubsitution(context.signals.done, ir.UInt(1)),
                ver.NonBlockingSubsitution(context.state_var, context.idle_state),
            ],
            else_body=[
                ver.NonBlockingSubsitution(context.state_var, context.done_state),
            ],
        )

    def new_caseitem(self, root: ir.Node):
        """
        Creates a new case item with the root's unique id as identifier
        """
        stmts = self.do_vertex(root)
        logging.debug("new caseitem %s", root.unique_id)
        item = ver.CaseItem(condition=ir.State(root.unique_id), statements=stmts)

        return item

    def do_vertex(self, vertex: ir.Node):
        """
        Processes a node
        """
        logging.debug("%s %s %s", self.do_vertex.__name__, vertex, len(self.visited))

        assert isinstance(vertex, ir.Node), str(vertex)
        self.visited.add(vertex.unique_id)

        stmts: list[ver.Statement] = []

        if isinstance(vertex, ir.AssignNode):
            stmts.append(
                ver.NonBlockingSubsitution(
                    vertex.lvalue,
                    vertex.rvalue,
                    comment=vertex.unique_id if self.config.add_debug_comments else "",
                )
            )
            stmts += self.do_edge(vertex.optimal_child)

        elif isinstance(vertex, ir.IfElseNode):
            then_body = self.do_edge(vertex.optimal_true_edge)
            else_body = self.do_edge(vertex.optimal_false_edge)
            stmts.append(
                ver.IfElse(
                    condition=vertex.condition,
                    then_body=then_body,
                    else_body=else_body,
                    comment=vertex.unique_id if self.config.add_debug_comments else "",
                )
            )
        else:
            raise TypeError(type(vertex))

        return stmts

    def do_edge(self, edge: ir.Edge):
        """
        Processes a edge
        """
        if isinstance(edge, ir.NonClockedEdge):
            return self.do_vertex(edge.optimal_child)
        if isinstance(edge, ir.ClockedEdge):
            if edge.optimal_child.unique_id not in self.visited:
                self.case.case_items.append(self.new_caseitem(edge.optimal_child))
            return [
                ver.NonBlockingSubsitution(
                    self.context.state_var, ir.State(edge.optimal_child.unique_id)
                )
            ]
        if isinstance(edge, type(None)):
            return []
        raise RuntimeError(f"{type(edge)}")
