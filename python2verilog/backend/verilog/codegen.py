"""
Verilog Codegen
"""

import itertools
import logging
import warnings
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
        self._context = context
        root_case = CaseBuilder(root, context).case
        counter = 0

        for item in root_case.case_items:
            # self._context.global_vars[item.condition.to_string()] = str(counter)
            self._context.add_state(item.condition.to_string())
            counter += 1

        # self._context.global_vars["_statelmaodone"] = str(counter)
        self._context.add_state_weak("_statelmaodone")

        self._context.global_vars["_state"] = self._context.exit

        self._module = CodeGen.__new_module(root_case, self._context)

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
            inputs.append(var)
        outputs = []
        for i in range(len((context.output_vars))):
            outputs.append(f"_out{str(i)}")
        # TODO: make these extras optional
        always = ver.PosedgeSyncAlways(
            ver.Expression("_clock"),
            valid="_valid",
            body=[CodeGen.__get_start_ifelse(root, context.global_vars, context.entry)],
        )
        body: list[ver.Statement] = [
            ver.Declaration(v, is_reg=True, is_signed=True) for v in context.global_vars
        ]
        body.append(always)

        state_vars = {key: str(index) for index, key in enumerate(context.state_vars)}
        return ver.Module(
            name=context.name,
            inputs=inputs,
            outputs=outputs,
            body=body,
            localparams=state_vars,
        )

    @staticmethod
    def __get_start_ifelse(root: ver.Case, global_vars: dict[str, str], entry: str):
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
        init_body: list[ver.Statement] = [ver.NonBlockingSubsitution("_ready", "0")]
        init_body += [
            ver.NonBlockingSubsitution(key, val) for key, val in global_vars.items()
        ]
        for item in root.case_items:
            # TODO: context.entry really should be a ver.Expression
            if str(item.condition) == entry:
                init_body += item.statements
                root.case_items.remove(item)
                break

        block = ver.IfElse(
            ver.Expression("_start"),
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
            string += "%0d, " * (len(self._context.output_vars) - 1)
            string += '%0d", _valid'
            for var in self._context.output_vars:
                string += f", {var}"
            string += ");"
            return ver.Statement(literal=string)

        assert isinstance(self._context, ir.Context)
        decl: list[ver.Declaration] = []
        decl.append(ver.Declaration("_clock", size=1, is_reg=True))
        decl.append(ver.Declaration("_start", size=1, is_reg=True))
        decl.append(ver.Declaration("_reset", size=1, is_reg=True))
        decl += [
            ver.Declaration(var, is_signed=True, is_reg=True)
            for var in self._context.input_vars
        ]
        decl += [
            ver.Declaration(var, is_signed=True) for var in self._context.output_vars
        ]

        decl.append(ver.Declaration("_ready", size=1))
        decl.append(ver.Declaration("_valid", size=1))

        ports = {
            decl.name: decl.name for decl in decl
        }  # Caution: expects decl to only contain declarations

        setups: list[ver.Statement] = list(decl)
        setups.append(ver.Instantiation(self._context.name, "DUT", ports))

        setups.append(ver.Statement(literal="always #5 _clock = !_clock;"))

        initial_body: list[
            ver.Statement | ver.While
        ] = []  # TODO: replace with Sequence
        initial_body.append(ver.BlockingSubsitution("_clock", "0"))
        initial_body.append(ver.BlockingSubsitution("_start", "0"))
        initial_body.append(ver.BlockingSubsitution("_reset", "1"))
        initial_body.append(ver.AtNegedgeStatement(ver.Expression("_clock")))
        initial_body.append(ver.BlockingSubsitution("_reset", "0"))
        initial_body.append(ver.Statement())

        for i, test_case in enumerate(test_cases):
            # setup for new test case
            initial_body.append(
                ver.Statement(comment=f"Test case {i}: {str(test_case)}")
            )
            for i, var in enumerate(self._context.input_vars):
                initial_body.append(ver.BlockingSubsitution(var, str(test_case[i])))
            initial_body.append(ver.BlockingSubsitution("_start", "1"))

            initial_body.append(ver.AtNegedgeStatement(ver.Expression("_clock")))

            # wait for done signal
            while_body: list[ver.Statement] = []
            while_body.append(ver.BlockingSubsitution("_start", "0"))
            while_body.append(make_display_stmt())
            while_body.append(ver.AtNegedgeStatement(ver.Expression("_clock")))

            initial_body.append(
                ver.While(condition=ver.Expression("!_ready"), body=while_body)
            )
            initial_body.append(make_display_stmt())
            initial_body.append(ver.Statement())

        initial_body.append(ver.Statement(literal="$finish;"))

        initial_loop = ver.Initial(body=initial_body)

        if self._context:
            module = ver.Module(
                f"{self._context.name}_tb",
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
        self.case = ver.Case(expression=ver.Expression("_state"), case_items=[])

        # Member Funcs
        instance = itertools.count()
        self.next_unique = lambda: next(instance)

        # Work
        self.case.case_items.append(self.new_caseitem(root))
        # logging.info(self.case.to_string())

    def new_caseitem(self, root: ir.Vertex):
        """
        Creates a new case item with the root's unique id as identifier
        """
        stmts = self.do_vertex(root)
        item = ver.CaseItem(condition=ver.Expression(root.unique_id), statements=stmts)

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
                ver.NonBlockingSubsitution("_ready", "1"),
                ver.NonBlockingSubsitution(
                    self.case.condition.to_string(), "_statelmaodone"
                ),
            ]

        elif isinstance(vertex, ir.AssignNode):
            stmts.append(
                ver.NonBlockingSubsitution(str(vertex.lvalue), str(vertex.rvalue))
            )
            stmts += self.do_edge(vertex.optimal_child)

        elif isinstance(vertex, ir.IfElseNode):
            then_body = self.do_edge(vertex.optimal_true_edge)
            else_body = self.do_edge(vertex.optimal_false_edge)
            stmts.append(
                ver.IfElse(
                    condition=ver.Expression(str(vertex.condition)),
                    then_body=then_body,
                    else_body=else_body,
                )
            )

        elif isinstance(vertex, ir.YieldNode):
            outputs = [
                ver.NonBlockingSubsitution(f"_out{i}", str(expr))
                for i, expr in enumerate(vertex.stmts)
            ] + [ver.NonBlockingSubsitution("_valid", "1")]
            state_change = []

            if isinstance(vertex.optimal_child.optimal_child, ir.DoneNode):
                outputs.append(ver.NonBlockingSubsitution("_ready", "1"))

            state_change.append(
                ver.NonBlockingSubsitution(
                    "_state", str(vertex.optimal_child.optimal_child.unique_id)
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
                ver.NonBlockingSubsitution("_state", str(edge.optimal_child.unique_id))
            ]
        raise RuntimeError(f"{type(edge)}")
