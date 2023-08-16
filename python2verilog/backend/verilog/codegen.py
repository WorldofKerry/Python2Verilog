"""
Verilog Codegen
"""

import itertools
import logging
import warnings

from python2verilog.optimizer.optimizer import backwards_replace
from . import ast as ver
from ... import ir
from ...utils.assertions import assert_type, assert_list_type, assert_dict_type


class CodeGen:
    """
    Code Generator for Verilog
    """

    def __init__(self, root: ir.Vertex, context: ir.Context):
        """ "
        Builds tree from Graph IR
        """
        assert_type(root, ir.Vertex)
        assert_type(context, ir.Context)
        self.context = context
        root_case = CaseBuilder(root, context).case

        for item in root_case.case_items:
            self.context.add_state(item.condition.to_string())

        self.context.add_state_weak(context.ready_state)

        self.context.add_global_var(
            ir.InputVar("state", initial_value=self.context.ready_state)
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
            ir.Expression("_clock"),
            body=[
                ver.NonBlockingSubsitution(context.valid_signal, ir.UInt(0)),
                ver.NonBlockingSubsitution(context.ready_signal, ir.UInt(0)),
            ]
            + [
                ver.NonBlockingSubsitution(out, ir.Int(0))
                for out in context.output_vars
            ]
            + [
                ver.IfElse(
                    ir.Expression("_reset"),
                    then_body=[
                        ver.NonBlockingSubsitution(
                            lvalue=context.state_var,
                            rvalue=ir.Expression(context.ready_state),
                        )
                    ],
                    else_body=[],
                )
            ]
            + [CodeGen.__get_start_ifelse(root, context)],
        )
        body: list[ver.Statement] = [
            ver.Declaration(v, is_reg=True, is_signed=True) for v in context.global_vars
        ]
        body += [
            ver.Declaration(var.ver_name, is_reg=True, is_signed=True)
            for var in context.input_vars
        ]

        body.append(always)

        state_vars = {key: ir.UInt(index) for index, key in enumerate(context.states)}

        return ver.Module(
            name=context.name,
            inputs=inputs,
            outputs=outputs,
            body=body,
            localparams=state_vars,
        )

    @staticmethod
    def __get_start_ifelse(root: ver.Case, context: ir.Context):
        """
        if (_start) begin
            <var> = <value>;
            ...
        end else begin
            case(...)
            ...
            endcase
        end
        """
        # The first case can be included here
        mapping = {
            ir.Expression(var.ver_name): ir.Expression(var.py_name)
            for var in context.input_vars
        }
        stmt_stack = []
        init_body = []

        for item in root.case_items:
            if item.condition == ir.Expression(context.entry):
                stmt_stack += item.statements
                init_body += item.statements
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

        for var in context.input_vars:
            init_body.append(
                ver.NonBlockingSubsitution(
                    ir.Expression(var.ver_name), ir.Expression(var.py_name)
                )
            )

        block = ver.IfElse(
            ir.Expression("_start"),
            init_body,
            [root],
        )
        return block

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

    def new_testbench(self, test_cases: list[tuple[str]]):
        """
        Creates testbench with multiple test cases

        Each element of test_cases represents a single test case
        """

        def make_display_stmt():
            """
            Creates a display statement for valid + outputs

            $display("%0d, ...", _valid, ...);
            """
            string = '$display("%0d, '
            string += "%0d, " * (len(self.context.output_vars) - 1)
            string += '%0d", _valid'
            for var in self.context.output_vars:
                string += f", {var}"
            string += ");"
            return ver.Statement(literal=string)

        assert isinstance(self.context, ir.Context)
        decl: list[ver.Declaration] = []
        decl.append(ver.Declaration("_clock", size=1, is_reg=True))
        decl.append(ver.Declaration("_start", size=1, is_reg=True))
        decl.append(ver.Declaration("_reset", size=1, is_reg=True))
        decl += [
            ver.Declaration(var.ver_name, is_signed=True)
            for var in self.context.output_vars
        ]
        decl += [
            ver.Declaration(var.py_name, is_signed=True, is_reg=True)
            for var in self.context.input_vars
        ]
        decl.append(ver.Declaration("_ready", size=1))
        decl.append(ver.Declaration("_valid", size=1))

        ports = {decl.name: decl.name for decl in decl}

        setups: list[ver.Statement] = list(decl)
        setups.append(ver.Instantiation(self.context.name, "DUT", ports))

        setups.append(ver.Statement(literal="always #5 _clock = !_clock;"))

        initial_body: list[ver.Statement | ver.While] = []
        initial_body.append(
            ver.BlockingSubsitution(self.context.clock_signal, ir.UInt(0))
        )
        initial_body.append(
            ver.BlockingSubsitution(self.context.start_signal, ir.UInt(0))
        )
        initial_body.append(
            ver.BlockingSubsitution(self.context.reset_signal, ir.UInt(1))
        )
        initial_body.append(ver.AtNegedgeStatement(self.context.clock_signal))
        initial_body.append(
            ver.BlockingSubsitution(self.context.reset_signal, ir.UInt(0))
        )
        initial_body.append(ver.Statement())

        for i, test_case in enumerate(test_cases):
            # setup for new test case
            initial_body.append(
                ver.Statement(comment=f"Test case {i}: {str(test_case)}")
            )
            for i, var in enumerate(self.context.input_vars):
                initial_body.append(
                    ver.BlockingSubsitution(
                        ir.Expression(var.py_name), ir.Int(int(test_case[i]))
                    )
                )
            initial_body.append(
                ver.BlockingSubsitution(self.context.start_signal, ir.UInt(1))
            )

            initial_body.append(ver.AtNegedgeStatement(self.context.clock_signal))

            # wait for done signal
            while_body: list[ver.Statement] = []
            while_body.append(
                ver.BlockingSubsitution(self.context.start_signal, ir.UInt(0))
            )
            while_body.append(make_display_stmt())
            while_body.append(ver.AtNegedgeStatement(self.context.clock_signal))

            initial_body.append(
                ver.While(
                    condition=ir.UnaryOp("!", self.context.ready_signal),
                    body=while_body,
                )
            )
            initial_body.append(make_display_stmt())
            initial_body.append(ver.Statement())

        initial_body.append(ver.Statement(literal="$finish;"))

        initial_loop = ver.Initial(body=initial_body)

        if self.context:
            module = ver.Module(
                f"{self.context.name}_tb",
                [],
                [],
                body=setups + [initial_loop],
                add_default_ports=False,
            )
            return module
        raise RuntimeError("Needs the context")

    def new_testbench_lines(self, test_cases: list[tuple[str]]):
        """
        New Testbench as lines
        """
        return self.new_testbench(test_cases).to_lines()

    def new_testbench_str(self, test_cases: list[tuple[str]]):
        """
        New testbench as str
        """
        return str(self.new_testbench_lines(test_cases))


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
        if not self.added_ready_node:
            self.case.case_items.append(
                ver.CaseItem(
                    ir.Expression(context.ready_state),
                    statements=[
                        ver.NonBlockingSubsitution(
                            lvalue=ir.State("_ready"), rvalue=ir.UInt(1)
                        )
                    ],
                )
            )

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
        assert isinstance(vertex, ir.Vertex)
        self.visited.add(vertex.unique_id)

        stmts: list[ver.Statement] = []

        if isinstance(vertex, ir.DoneNode):
            stmts += [
                ver.NonBlockingSubsitution(self.context.ready_signal, ir.UInt(1)),
                ver.NonBlockingSubsitution(
                    self.case.condition, ir.Expression(self.context.ready_state)
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
            ] + [ver.NonBlockingSubsitution(self.context.valid_signal, ir.UInt(1))]
            state_change = []

            if isinstance(vertex.optimal_child.optimal_child, ir.DoneNode):
                outputs.append(
                    ver.NonBlockingSubsitution(self.context.ready_signal, ir.UInt(1))
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

            # stmts += outputs + self.do_edge(vertex.optimal_child)
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
