"""
Verilog Codegen
"""

import itertools
import typing

from python2verilog.optimizer.optimizer import backwards_replace
from python2verilog.utils.string import Lines

from ... import ir
from ...utils.assertions import assert_typed_dict, get_typed, get_typed_list
from . import ast as ver


class CodeGen:
    """
    Code Generator for Verilog
    """

    def __init__(self, root: ir.Vertex, context: ir.Context):
        """ "
        Builds tree from Graph IR
        """
        get_typed(root, ir.Vertex)
        get_typed(context, ir.Context)
        self.context = context

        self.context.output_vars = [
            ir.Var(str(i)) for i in range(len(self.context.output_types))
        ]

        root_case = CaseBuilder(root, context).case

        for item in root_case.case_items:
            self.context.add_state_weak(
                item.condition.to_string()
            )  # change to not weak

        assert isinstance(context.done_state, str)
        self.context.add_state_weak(context.done_state)

        self.context.add_global_var(
            ir.Var("state", initial_value=self.context.done_state)
        )

        self._module = CodeGen.__new_module(root_case, self.context)

    @staticmethod
    def __new_module(root: ver.Case, context: ir.Context):
        """
        Creates a module wrapper from the context

        Requires context for I/O and declarations
        """
        assert isinstance(root, ver.Statement)
        assert isinstance(context, ir.Context)

        inputs = []
        for var in context.input_vars:
            inputs.append(var.py_name)

        outputs = []
        for var in context.output_vars:
            outputs.append(var.ver_name)

        always = ver.PosedgeSyncAlways(
            context.signals.clock_signal,
            body=[
                ver.NonBlockingSubsitution(context.signals.done_signal, ir.UInt(0)),
                ver.Statement(),
                ver.IfElse(
                    context.signals.ready_signal,
                    typing.cast(
                        list[ver.Statement],
                        [
                            ver.NonBlockingSubsitution(
                                context.signals.valid_signal, ir.UInt(0)
                            )
                        ],
                    ),
                    [],
                ),
            ]
            + [
                ver.Statement(),
                ver.Statement(comment="Start signal takes precedence over reset"),
                ver.IfElse(
                    context.signals.reset_signal,
                    then_body=[
                        ver.NonBlockingSubsitution(
                            lvalue=context.state_var,
                            rvalue=ir.Expression(context.done_state),
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
            ver.Statement(comment="Global variables"),
        ]

        body += [ver.Declaration(v, reg=True, signed=True) for v in context.global_vars]

        body += [
            ver.Declaration(var.ver_name, reg=True, signed=True)
            for var in context.input_vars
        ]

        for instance in context.instances.values():
            body.append(
                ver.Statement(
                    comment="================ Function Instance ================"
                )
            )
            module = context.namespace[instance.module_name]
            defaults = {
                module.signals.valid_signal: instance.signals.valid_signal,
                module.signals.done_signal: instance.signals.done_signal,
                module.signals.clock_signal: context.signals.clock_signal,
                module.signals.start_signal: instance.signals.start_signal,
                module.signals.reset_signal: instance.signals.reset_signal,
                module.signals.ready_signal: instance.signals.ready_signal,
            }
            # defaults = dict(zip(module.signals.values(), instance.signals.values()))
            for var in instance.inputs:
                body.append(ver.Declaration(name=var.ver_name, reg=True))
            for var in instance.outputs:
                body.append(ver.Declaration(name=var.ver_name))
            body.append(
                ver.Declaration(name=instance.signals.valid_signal.ver_name, size=1)
            )
            body.append(
                ver.Declaration(name=instance.signals.done_signal.ver_name, size=1)
            )
            body.append(
                ver.Declaration(
                    name=instance.signals.start_signal.ver_name, size=1, reg=True
                )
            )
            body.append(
                ver.Declaration(
                    name=instance.signals.ready_signal.ver_name, size=1, reg=True
                )
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

        python_test_code = Lines()
        for case in context.test_cases:
            python_test_code += f"print(list({context.name}(*{case})))"
        return ver.Module(
            name=context.name,
            inputs=inputs,
            outputs=outputs,
            body=body,
            localparams=state_vars,
            header=Lines(
                f"/*\n\n# Python Function\n{context.py_string}\n\n"
                f"# Test Cases\n{python_test_code}\n*/\n\n"
            ),
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
        # The first case can be included here
        mapping = {
            ir.Expression(var.ver_name): ir.Expression(var.py_name)
            for var in context.input_vars
        }

        then_body: list[ver.Statement] = []
        for var in context.input_vars:
            then_body.append(
                ver.NonBlockingSubsitution(
                    ir.Expression(var.ver_name), ir.Expression(var.py_name)
                )
            )

        stmt_stack: list[ver.Statement] = []  # backwards replace using dfs
        for item in root.case_items:
            if item.condition == ir.Expression(context.entry_state):
                stmt_stack += item.statements
                then_body += item.statements
                root.case_items.remove(item)
                break

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

        if_else = ver.IfElse(
            ir.Expression("_start"),
            then_body,
            [
                ver.Statement(
                    comment="If ready or not valid, then continue computation"
                ),
                ver.IfElse(
                    ir.UBinOp(
                        context.signals.ready_signal,
                        "||",
                        ir.UnaryOp("!", context.signals.valid_signal),
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
        return str(self.get_module_lines())

    def get_testbench(self, random_wait: bool = False):
        """
        Creates testbench with multiple test cases

        Each element of self.context.test_cases represents a single test case

        :param random_wait: whether or not to have random _wait signal in the while loop
        """
        if len(self.context.input_vars) == 0:
            raise RuntimeError(f"Input var names not deduced for {self.context.name}")
        if len(self.context.output_vars) == 0:
            raise RuntimeError(
                f"Output var types not deduced for {self.context.name}, \
                    types are {self.context.output_types}"
            )

        def make_display_stmt():
            """
            Creates a display statement for valid + outputs

            $display("%0d, ...", _valid, ...);
            """
            string = '$display("%0d, %0d, '
            string += "%0d, " * (len(self.context.output_vars) - 1)
            string += '%0d", _valid, _ready'
            for var in self.context.output_vars:
                string += f", {var}"
            string += ");"
            return ver.Statement(literal=string)

        assert isinstance(self.context, ir.Context)
        decl: list[ver.Declaration] = []
        decl.append(ver.Declaration("_clock", size=1, reg=True))
        decl.append(ver.Declaration("_start", size=1, reg=True))
        decl.append(ver.Declaration("_reset", size=1, reg=True))
        decl.append(ver.Declaration("_ready", size=1, reg=True))
        decl += [
            ver.Declaration(var.py_name, signed=True, reg=True)
            for var in self.context.input_vars
        ]
        decl.append(ver.Declaration("_done", size=1))
        decl.append(ver.Declaration("_valid", size=1))
        decl += [
            ver.Declaration(var.ver_name, signed=True)
            for var in self.context.output_vars
        ]

        ports = {decl.name: decl.name for decl in decl}

        setups: list[ver.Statement] = list(decl)
        setups.append(ver.Instantiation(self.context.name, "DUT", ports))

        setups.append(ver.Statement(literal="always #5 _clock = !_clock;"))

        initial_body: list[ver.Statement | ver.While] = []
        initial_body.append(
            ver.BlockingSub(self.context.signals.clock_signal, ir.UInt(0))
        )
        initial_body.append(
            ver.BlockingSub(self.context.signals.start_signal, ir.UInt(0))
        )
        initial_body.append(
            ver.BlockingSub(self.context.signals.ready_signal, ir.UInt(1))
        )
        initial_body.append(
            ver.BlockingSub(self.context.signals.reset_signal, ir.UInt(1))
        )

        initial_body.append(ver.AtNegedgeStatement(self.context.signals.clock_signal))
        initial_body.append(
            ver.BlockingSub(self.context.signals.reset_signal, ir.UInt(0))
        )
        initial_body.append(ver.Statement())

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
                        ir.Expression(var.py_name), ir.Int(int(test_case[i]))
                    )
                )
            initial_body.append(
                ver.BlockingSub(self.context.signals.start_signal, ir.UInt(1))
            )

            # Post-start
            initial_body.append(ver.Statement())
            initial_body.append(
                ver.AtNegedgeStatement(self.context.signals.clock_signal)
            )
            for i, var in enumerate(self.context.input_vars):
                initial_body.append(
                    ver.BlockingSub(
                        ir.Expression(var.py_name),
                        ir.Unknown(),
                        comment="only need inputs when start is set",
                    )
                )
            initial_body.append(
                ver.BlockingSub(self.context.signals.start_signal, ir.UInt(0))
            )
            initial_body.append(ver.Statement())

            # While loop waitng for ready signal
            while_body: list[ver.Statement] = []
            # while_body.append(make_display_stmt())
            if random_wait:
                while_body.append(ver.Statement("_ready = $urandom_range(0, 4) === 0;"))
            while_body.append(
                ver.Statement(
                    comment="`if (_ready && _valid)` also works as a conditional"
                )
            )
            while_body.append(
                ver.IfElse(
                    condition=ir.Expression("_ready"),
                    then_body=[make_display_stmt()],
                    else_body=[],
                )
            )
            while_body.append(ver.AtNegedgeStatement(self.context.signals.clock_signal))

            initial_body.append(
                ver.While(
                    condition=ir.UBinOp(
                        ir.UnaryOp("!", self.context.signals.done_signal),
                        "||",
                        ir.UnaryOp("!", self.context.signals.ready_signal),
                    ),
                    body=while_body,
                )
            )
            initial_body.append(
                ver.IfElse(
                    condition=ir.Expression("_ready"),
                    then_body=[make_display_stmt()],
                    else_body=[],
                )
            )
            initial_body.append(ver.Statement())

        initial_body.append(ver.Statement(literal="$finish;"))

        initial_loop = ver.Initial(body=initial_body)

        if self.context:
            module = ver.Module(
                f"{self.context.name}_tb",
                [],
                [],
                body=setups + [initial_loop],
                is_not_testbench=False,
            )
            return module
        raise RuntimeError("Needs the context")

    def get_testbench_lines(self, random_wait: bool = False):
        """
        New Testbench as lines
        """
        return self.get_testbench(random_wait=random_wait).to_lines()

    def get_testbench_str(self, random_wait: bool = False):
        """
        New testbench as str
        """
        return str(self.get_testbench_lines(random_wait=random_wait))


class CaseBuilder:
    """
    Creates a case statement for the IR Graph
    """

    def __init__(self, root: ir.Vertex, context: ir.Context):
        # Member Vars
        self.visited: set[str] = set()
        self.context = context
        self.case = ver.Case(expression=ir.Expression("_state"), case_items=[])
        self.added_ready_node = False

        # Member Funcs
        instance = itertools.count()
        self.next_unique = lambda: next(instance)

        # Work
        self.case.case_items.append(self.new_caseitem(root))
        have_done_state = False
        for caseitem in self.case.case_items:
            if context.done_state == str(caseitem.condition):
                have_done_state = True
        if not have_done_state:
            self.case.case_items.append(
                ver.CaseItem(
                    ir.Expression(context.done_state),
                    statements=[
                        ver.NonBlockingSubsitution(
                            lvalue=ir.State("_done"), rvalue=ir.UInt(1)
                        )
                    ],
                )
            )

        # If optimizer removes done node
        # if ir.Expression(context)

    def new_caseitem(self, root: ir.Vertex):
        """
        Creates a new case item with the root's unique id as identifier
        """
        stmts = self.do_vertex(root)
        item = ver.CaseItem(condition=ir.Expression(root.unique_id), statements=stmts)

        return item

    def do_vertex(self, vertex: ir.Vertex):
        """
        Processes a node
        """
        assert isinstance(vertex, ir.Vertex), str(vertex)
        self.visited.add(vertex.unique_id)

        stmts: list[ver.Statement] = []

        if isinstance(vertex, ir.DoneNode):
            stmts += [
                ver.NonBlockingSubsitution(
                    self.context.signals.done_signal, ir.UInt(1)
                ),
                ver.NonBlockingSubsitution(
                    self.case.condition, ir.Expression(self.context.done_state)
                ),
            ]
            self.added_ready_node = True

        elif isinstance(vertex, ir.AssignNode):
            stmts.append(ver.NonBlockingSubsitution(vertex.lvalue, vertex.rvalue))
            stmts += self.do_edge(vertex.optimal_child)

        elif isinstance(vertex, ir.IfElseNode):
            then_body = self.do_edge(vertex.optimal_true_edge)
            else_body = self.do_edge(vertex.optimal_false_edge)
            stmts.append(
                ver.IfElse(
                    condition=vertex.condition,
                    then_body=then_body,
                    else_body=else_body,
                )
            )

        elif isinstance(vertex, ir.YieldNode):
            outputs = [
                ver.NonBlockingSubsitution(var, expr)
                for var, expr in zip(self.context.output_vars, vertex.stmts)
            ] + [
                ver.NonBlockingSubsitution(
                    self.context.signals.valid_signal, ir.UInt(1)
                )
            ]
            state_change = []

            if isinstance(vertex.optimal_child.optimal_child, ir.DoneNode):
                outputs.append(
                    ver.NonBlockingSubsitution(
                        self.context.signals.done_signal, ir.UInt(1)
                    )
                )

            state_change.append(
                ver.NonBlockingSubsitution(
                    self.context.state_var,
                    ir.Expression(vertex.optimal_child.optimal_child.unique_id),
                )
            )
            if vertex.optimal_child.optimal_child.unique_id not in self.visited:
                self.case.case_items.append(
                    self.new_caseitem(vertex.optimal_child.optimal_child)
                )

            stmts += outputs + state_change

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
                    self.context.state_var, ir.Expression(edge.optimal_child.unique_id)
                )
            ]
        raise RuntimeError(f"{type(edge)}")
