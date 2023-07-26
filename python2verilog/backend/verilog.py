"""Verilog Abstract Syntax Tree Components"""

from __future__ import annotations
import warnings
import ast
from typing import Optional
import copy

from ..utils.string import Lines, Indent, ImplementsToLines
from ..utils.assertions import assert_list_type, assert_type, assert_dict_type
from .. import ir


class Expression:
    """
    Verilog expression, e.g.
    a + b
    Currently just a string
    """

    def __init__(self, expr: str):
        assert isinstance(expr, str)
        self.expr = expr

    def to_string(self):
        """
        To Verilog
        """
        return self.expr


class AtPosedge(Expression):
    """
    @(posedge <condition>)
    """

    def __init__(self, condition: Expression):
        assert isinstance(condition, Expression)
        self.condition = condition
        super().__init__(f"@(posedge {condition.to_string()})")


class AtNegedge(Expression):
    """
    @(negedge <condition>)
    """

    def __init__(self, condition: Expression):
        assert isinstance(condition, Expression)
        self.condition = condition
        super().__init__(f"@(negedge {condition.to_string()})")


class Statement(ImplementsToLines):
    """
    Represents a statement in verilog (i.e. a line or a block)
    If used directly, it is treated as a string literal
    """

    def __init__(self, literal: str = "", comment: str = ""):
        self.literal = literal
        self.comment = comment

    def to_lines(self):
        """
        To Verilog
        """
        if self.literal:
            return Lines(
                self.literal + self.get_inline_comment()[1:]
            )  # Removes leading space
        return Lines(self.get_inline_comment()[1:])

    def get_inline_comment(self):
        """
        // <comment>
        """
        if self.comment != "":
            return f" // {self.comment}"
        return ""

    def get_blocked_comment(self):
        """
        // <comment>
        ...
        // <comment>
        Separated by newlines
        """
        actual_lines = self.comment.split("\n")
        lines = Lines()
        for line in actual_lines:
            lines += f"// {line}"
        return lines


class AtPosedgeStatement(Statement):
    """
    @(posedge <condition>);
    """

    def __init__(self, condition: Expression, *args, **kwargs):
        assert isinstance(condition, Expression)
        super().__init__(f"{AtPosedge(condition).to_string()};", *args, **kwargs)


class AtNegedgeStatement(Statement):
    """
    @(negedge <condition>);
    """

    def __init__(self, condition: Expression, *args, **kwargs):
        assert isinstance(condition, Expression)
        super().__init__(f"{AtNegedge(condition).to_string()};", *args, **kwargs)


class Verilog:
    """
    Code Generation for Verilog
    """

    @staticmethod
    def __new_module(root: Statement, context: ir.Context):
        """
        Creates a module wrapper from the context

        Requires context for I/O and declarations
        """
        assert isinstance(root, Statement)
        assert isinstance(context, ir.Context)
        inputs = []
        for var in context.input_vars:
            inputs.append(var)
        outputs = []
        for i in range(len((context.output_vars))):
            outputs.append(f"_out{str(i)}")
        # TODO: make these extras optional
        always = PosedgeSyncAlways(
            Expression("_clock"),
            valid="_valid",
            body=[Verilog.__get_start_ifelse(root, context.global_vars)],
        )
        body: list[Statement] = [
            Declaration(v, is_reg=True, is_signed=True) for v in context.global_vars
        ]
        body.append(always)
        return Module(name=context.name, inputs=inputs, outputs=outputs, body=body)

    def __init__(self):
        self._context = None
        self._module = None

    @classmethod
    def from_list_ir(cls, root: ir.Statement, context: ir.Context):
        """
        Builds tree from list IR
        """
        assert isinstance(root, ir.Statement), f"got {type(root)} instead"
        assert isinstance(context, ir.Context)
        inst = Verilog()
        inst._context = context
        inst._module = Verilog.__new_module(Verilog.list_build_stmt(root), context)
        return inst

    @classmethod
    def from_graph_ir(cls, root: ir.Node, context: ir.Context):
        """ "
        Builds tree from Graph IR
        """
        assert_type(root, ir.Node)
        assert_type(context, ir.Context)
        inst = Verilog()
        inst._context = context
        root_case = inst.graph_build(root, set())
        inst._context.global_vars["_state"] = str(len(root_case.case_items))
        inst._module = Verilog.__new_module(root_case, context)
        return inst

    @staticmethod
    def list_build_stmt(node: ir.Statement) -> Statement:
        """
        Builds the Verilog AST
        """
        assert isinstance(node, (ir.Statement, ir.CaseItem))
        if not node:
            return Statement("")
        if isinstance(node, ir.Case):
            return Verilog.list_build_case(node)
        if isinstance(node, ir.IfElse):
            then_body = []
            for stmt in node.then_body:
                then_body.append(Verilog.list_build_stmt(stmt))
            else_body = []
            for stmt in node.else_body:
                else_body.append(Verilog.list_build_stmt(stmt))
            return IfElse(Verilog.list_build_expr(node.condition), then_body, else_body)
        if isinstance(node, ir.Statement):
            return Statement(node.to_string().replace("\n", " "))
        raise NotImplementedError(f"Unexpected type {type(node)}")

    @staticmethod
    def list_build_expr(node: ir.Expression) -> Expression:
        """
        Handles expressions
        """
        assert isinstance(node, ir.Expression)
        return Expression(node.to_string())

    @staticmethod
    def list_build_case(node: ir.Case) -> Case:
        """
        Handles case statements
        """
        assert isinstance(node, ir.Case)
        case_items = []
        for item in node.case_items:
            case_items.append(Verilog.list_build_case_item(item))
        return Case(Verilog.list_build_expr(node.condition), case_items)

    @staticmethod
    def list_build_case_item(node: ir.CaseItem) -> CaseItem:
        """
        Handles case item
        """
        case_items = []
        for item in node.statements:
            case_items.append(Verilog.list_build_stmt(item))
        return CaseItem(Verilog.list_build_expr(node.condition), case_items)

    def graph_build(self, root: ir.Node, visited: set[str]):
        """
        Builds from graph
        """
        assert_type(root, ir.Node)
        root_case = Case(expression=Expression("_state"), case_items=[])
        self.graph_build_node(node=root, root_case=root_case, visited=visited)
        return root_case

    def graph_build_node(self, node: ir.Node, root_case: Case, visited: set[str]):
        """
        Builds from node
        """
        assert_type(node, ir.Node)
        assert isinstance(self._context, ir.Context)
        if node.unique_id in visited:
            return node.unique_id

        if isinstance(node, ir.AssignNode):
            if node.unique_id not in visited:
                visited.add(node.unique_id)
                next_state = self.graph_build_node(node._edge, root_case, visited)
                root_case.case_items.append(
                    CaseItem(
                        condition=Expression(node.unique_id),
                        statements=[
                            Statement(f"{node.to_string()};"),
                            NonBlockingSubsitution(
                                lvalue=root_case.condition.to_string(),
                                rvalue=next_state,
                            ),
                        ],
                    )
                )
                self._context.global_vars[node.unique_id] = len(root_case.case_items)
            return node.unique_id
        if isinstance(node, ir.IfElseNode):
            if node.unique_id not in visited:
                visited.add(node.unique_id)
                then_state = self.graph_build_node(node._then_edge, root_case, visited)
                else_state = self.graph_build_node(node._else_edge, root_case, visited)
                root_case.case_items.append(
                    CaseItem(
                        condition=Expression(node.unique_id),
                        statements=[
                            IfElse(
                                condition=Expression(node._condition.to_string()),
                                then_body=[
                                    NonBlockingSubsitution(
                                        root_case.condition.to_string(), then_state
                                    )
                                ],
                                else_body=[
                                    NonBlockingSubsitution(
                                        root_case.condition.to_string(), else_state
                                    )
                                ],
                            )
                        ],
                    )
                )
                self._context.global_vars[node.unique_id] = len(root_case.case_items)
            return node.unique_id
        if isinstance(node, ir.YieldNode):
            if node.unique_id not in visited:
                visited.add(node.unique_id)
                next_state = self.graph_build_node(node._edge, root_case, visited)
                stmts = [
                    NonBlockingSubsitution(f"_out{i}", v.to_string())
                    for i, v in enumerate(node._stmts)
                ] + [NonBlockingSubsitution("_valid", "1")]
                root_case.case_items.append(
                    CaseItem(
                        condition=Expression(node.unique_id),
                        statements=[
                            *stmts,
                            NonBlockingSubsitution(
                                lvalue=root_case.condition.to_string(),
                                rvalue=next_state,
                            ),
                        ],
                    )
                )
                self._context.global_vars[node.unique_id] = len(root_case.case_items)
            return node.unique_id
        if isinstance(node, ir.Edge):
            if node.unique_id not in visited:
                visited.add(node.unique_id)
                return self.graph_build_node(node._node, root_case, visited)
            return "bruvlmao"
        if isinstance(node, ir.Node):
            if node.unique_id not in visited:
                visited.add(node.unique_id)
                root_case.case_items.append(
                    CaseItem(
                        condition=Expression(node.unique_id),
                        statements=[
                            NonBlockingSubsitution("_done", "1"),
                        ],
                    )
                )
                self._context.global_vars[node.unique_id] = len(root_case.case_items)
            return node.unique_id
        assert_type(node, ir.AssignNode)
        return ""

    @staticmethod
    def __get_start_ifelse(root: Statement, global_vars: dict[str, str]):
        """
        if (_start) begin
            <var> = <value>;
            ...
        end else begin
        ...
        end
        """
        then_body: list[Statement] = [NonBlockingSubsitution("_done", "0")]
        then_body += [
            NonBlockingSubsitution(key, str(val)) for key, val in global_vars.items()
        ]
        block = IfElse(
            Expression("_start"),
            then_body,
            [root],
        )
        return block

    @property
    def module(self):
        """
        Get Verilog module
        """
        assert isinstance(self._module, Module)
        return copy.deepcopy(self._module)

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
            return Statement(literal=string)

        assert isinstance(self._context, ir.Context)
        decl: list[Declaration] = []
        decl.append(Declaration("_clock", size=1, is_reg=True))
        decl.append(Declaration("_start", size=1, is_reg=True))
        decl += [
            Declaration(var, is_signed=True, is_reg=True)
            for var in self._context.input_vars
        ]
        decl += [Declaration(var, is_signed=True) for var in self._context.output_vars]

        decl.append(Declaration("_done", size=1))
        decl.append(Declaration("_valid", size=1))

        ports = {
            decl.name: decl.name for decl in decl
        }  # Caution: expects decl to only contain declarations

        setups: list[Statement] = list(decl)
        setups.append(Instantiation(self._context.name, "DUT", ports))

        setups.append(Statement(literal="always #5 _clock = !_clock;"))

        initial_body: list[Statement | While] = []  # TODO: replace with Sequence
        initial_body.append(BlockingSubsitution("_clock", "0"))
        initial_body.append(BlockingSubsitution("_start", "0"))
        initial_body.append(AtNegedgeStatement(Expression("_clock")))
        initial_body.append(Statement())

        for i, test_case in enumerate(test_cases):
            # setup for new test case
            initial_body.append(Statement(comment=f"Test case {i}: {str(test_case)}"))
            for i, var in enumerate(self._context.input_vars):
                initial_body.append(BlockingSubsitution(var, str(test_case[i])))
            initial_body.append(BlockingSubsitution("_start", "1"))

            initial_body.append(AtNegedgeStatement(Expression("_clock")))

            # wait for done signal
            while_body: list[Statement] = []
            while_body.append(BlockingSubsitution("_start", "0"))
            while_body.append(make_display_stmt())
            while_body.append(AtNegedgeStatement(Expression("_clock")))

            initial_body.append(While(condition=Expression("!_done"), body=while_body))
            initial_body.append(make_display_stmt())
            initial_body.append(Statement())

        initial_body.append(Statement(literal="$finish;"))

        initial_loop = Initial(body=initial_body)

        if self._context:
            module = Module(
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


class Instantiation(Statement):
    """
    Instantiationo f Verilog module.
    <module-name> <given-name> (...);
    """

    def __init__(
        self,
        module_name: str,
        given_name: str,
        port_connections: dict[str, str],
        *args,
        **kwargs,
    ):
        """
        port_connections[port_name] = signal_name, i.e. `.port_name(signal_name)`
        """
        assert isinstance(given_name, str)
        assert isinstance(module_name, str)
        for key, val in port_connections.items():
            assert isinstance(key, str)
            assert isinstance(val, str)
        self.given_name = given_name
        self.module_name = module_name
        self.port_connections = port_connections
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        To Verilog
        """
        lines = Lines()
        lines += f"{self.module_name} {self.given_name} ("
        for key, val in self.port_connections.items():
            lines += Indent(1) + f".{key}({val}),"
        lines[-1] = lines[-1][:-1]  # Remove last comma
        lines += Indent(1) + ");"
        return lines


class Module(ImplementsToLines):
    """
    module name(...); endmodule
    """

    def __init__(
        self,
        name: str,
        inputs: list[str],
        outputs: list[str],
        body: Optional[list[Statement]] = None,
        add_default_ports=True,
    ):
        self.name = name  # TODO: assert invalid names

        input_lines = Lines()
        for inputt in inputs:
            assert isinstance(inputt, str)
            input_lines += f"input wire [31:0] {inputt}"
        if add_default_ports:
            input_lines += "input wire _start"
            input_lines += "input wire _clock"
        self.input = input_lines

        output_lines = Lines()
        for output in outputs:
            assert isinstance(output, str)
            output_lines += f"output reg [31:0] {output}"
        if add_default_ports:
            output_lines += "output reg _done"
            output_lines += "output reg _valid"
        self.output = output_lines

        if body:
            for stmt in body:
                assert isinstance(stmt, Statement), f"got {type(stmt)} instead"
            self.body = body
        else:
            self.body = []

    def to_lines(self):
        """
        To Verilog
        """
        lines = Lines()
        lines += f"module {self.name} ("
        for line in self.input:
            lines += Indent(1) + line + ","
        for line in self.output:
            lines += Indent(1) + line + ","
        if len(lines) > 1:  # This means there are ports
            lines[-1] = lines[-1][0:-1]  # removes last comma
        lines += ");"
        for stmt in self.body:
            if stmt.to_lines() is None:
                warnings.warn(type(stmt))
            lines.concat(stmt.to_lines(), 1)
        lines += "endmodule"
        return lines


class Initial(Statement):
    """
    initial begin
        ...
    end
    """

    def __init__(self, *args, body: Optional[list[Statement]] = None, **kwargs):
        if body:
            assert_list_type(body, Statement)
        self.body = body
        super().__init__(*args, **kwargs)

    def to_lines(self):
        lines = Lines("initial begin")
        for stmt in self.body:
            lines.concat(stmt.to_lines(), 1)
        lines += "end"
        return lines


class Always(Statement):
    """
    always () begin
        ...
    end
    """

    def __init__(
        self,
        trigger: Expression,
        *args,
        body: Optional[list[Statement]] = None,
        valid: Optional[str] = None,
        **kwargs,
    ):
        assert isinstance(trigger, Expression)
        self.trigger = trigger
        if valid:
            self.valid: Optional[NonBlockingSubsitution] = NonBlockingSubsitution(
                valid, "0"
            )
        else:
            self.valid = None
        if body:
            for stmt in body:
                assert isinstance(stmt, Statement)
            self.body = body
        else:
            self.body = []
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        To Verilog
        """
        lines = Lines(f"always {self.trigger.to_string()} begin")
        if self.valid:
            lines.concat(self.valid.to_lines(), 1)
        lines.concat(NonBlockingSubsitution("_done", "0").to_lines(), 1)
        for stmt in self.body:
            lines.concat(stmt.to_lines(), 1)
        lines += "end"
        return lines


class PosedgeSyncAlways(Always):
    """
    always @(posedge <clock>) begin
        <valid> = 0;
    end
    """

    def __init__(self, clock: Expression, *args, **kwargs):
        assert isinstance(clock, Expression)
        self.clock = clock
        super().__init__(AtPosedge(clock), *args, **kwargs)


class Subsitution(Statement):
    """
    Interface for
    <lvalue> <blocking or nonblocking> <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, oper: str, *args, **kwargs):
        assert isinstance(
            rvalue, str
        ), f"got {type(rvalue)} instead"  # TODO: should eventually take an expression
        assert isinstance(lvalue, str)
        self.lvalue = lvalue
        self.rvalue = rvalue
        self.oper = oper
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        Converts to Verilog
        """
        assert isinstance(self.oper, str), "Subclasses need to set self.type"
        itself = f"{self.lvalue} {self.oper} {self.rvalue};"
        lines = Lines(itself)
        return lines


class NonBlockingSubsitution(Subsitution):
    """
    <lvalue> <= <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        super().__init__(lvalue, rvalue, "<=", *args, **kwargs)


class BlockingSubsitution(Subsitution):
    """
    <lvalue> = <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        super().__init__(lvalue, rvalue, "=", *args, *kwargs)


class Declaration(Statement):
    """
    <reg or wire> <modifiers> <[size-1:0]> <name>;
    """

    def __init__(
        self,
        name: str,
        *args,
        size: int = 32,
        is_reg: bool = False,
        is_signed: bool = False,
        **kwargs,
    ):
        self.size = size
        self.is_reg = is_reg
        self.is_signed = is_signed
        self.name = name
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        To Verilog lines
        """
        string = ""
        if self.is_reg:
            string += "reg"
        else:
            string += "wire"
        if self.is_signed:
            string += " signed"
        if self.size > 1:
            string += f" [{self.size-1}:0]"
        string += f" {self.name}"
        string += ";"
        return Lines(string)


class CaseItem:
    """
    Verilog case item, i.e.
    <condition>: begin
        <statements>
    end
    """

    def __init__(self, condition: Expression, statements: list[Statement]):
        assert isinstance(condition, Expression)
        self.condition = condition  # Can these by expressions are only literals?
        if statements:
            for stmt in statements:
                assert isinstance(stmt, Statement), f"unexpected {type(stmt)}"
            self.statements = statements
        else:
            self.statements = []

    def to_lines(self):
        """
        To Verilog lines
        """
        lines = Lines()
        lines += f"{self.condition.to_string()}: begin"
        for stmt in self.statements:
            lines.concat(stmt.to_lines(), indent=1)
        lines += "end"
        return lines

    def to_string(self):
        """
        To Verilog
        """
        return self.to_lines().to_string()


class Case(Statement):
    """
    Verilog case statement with various cases
    case (<expression>)
        <items[0]>
        ...
        <items[n]>
    endcase
    """

    def __init__(
        self, expression: Expression, case_items: list[CaseItem], *args, **kwargs
    ):
        assert isinstance(expression, Expression)
        self.condition = expression
        if case_items:
            for item in case_items:
                assert isinstance(item, CaseItem)
            self.case_items = case_items
        else:
            self.case_items = []
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        To Verilog Lines
        """
        lines = Lines()
        lines += f"case ({self.condition.to_string()})"
        for item in self.case_items:
            lines.concat(item.to_lines(), indent=1)
        lines += "endcase"
        return lines


class IfElse(Statement):
    """
    Verilog if else
    """

    def __init__(
        self,
        condition: Expression,
        then_body: list[Statement],
        else_body: list[Statement],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        assert isinstance(condition, Expression)
        self.condition = condition
        self.then_body = assert_list_type(then_body, Statement)
        self.else_body = assert_list_type(else_body, Statement)

    def to_lines(self):
        lines = Lines()
        lines += f"if ({self.condition.to_string()}) begin"
        for stmt in self.then_body:
            lines.concat(stmt.to_lines(), indent=1)
        lines += "end else begin"
        for stmt in self.else_body:
            lines.concat(stmt.to_lines(), indent=1)
        lines += "end"
        return lines

    def append_end_statements(self, statements: list[Statement]):
        """
        Appends statements to both branches
        """
        statements = assert_list_type(statements, Statement)
        # warnings.warn("appending " + statements[0].to_string())
        # if len(statements) > 1:
        #     warnings.warn(statements[1].to_string())
        self.then_body[-1].append_end_statements(statements)
        self.else_body[-1].append_end_statements(statements)
        return self


class While(Statement):
    """
    Unsynthesizable While
    while (<condition>) begin
        ...
    end
    """

    def __init__(
        self,
        *args,
        condition: Expression,
        body: Optional[list[Statement]] = None,
        **kwargs,
    ):
        assert isinstance(condition, Expression)
        self.condition = condition
        if body:
            assert_list_type(body, Statement)
        self.body = body
        super().__init__(*args, **kwargs)

    def to_lines(self):
        lines = Lines(f"while ({self.condition.to_string()}) begin")
        for stmt in self.body:
            lines.concat(stmt.to_lines(), 1)
        lines += "end"
        return lines
