"""Parser for Python Generator Functions"""

from __future__ import annotations
import ast
from .utils import Lines, Indent


class GeneratorParser:
    """
    Parses python generator functions
    """

    @staticmethod
    def generate_return_vars(node: ast.AST, prefix: str):
        """
        Generates the yielded variables of the function
        """
        assert isinstance(node, ast.Subscript)
        assert isinstance(node.slice, ast.Tuple)
        return [f"{prefix}_out{str(i)}" for i in range(len(node.slice.elts))]

    def create_unique_name(self):
        """
        Generates an id that is unique among all unique global variables
        """
        self.unique_name_counter += 1
        return f"{self.unique_name_counter}"

    def add_global_var(self, initial_value: str, name: str):
        """
        Adds global variables
        """
        self.global_vars[name] = initial_value
        return name

    @staticmethod
    def stringify_always_block():
        """
        always @(posedge _clock) begin
        end
        """
        return (Lines(["always @(posedge _clock) begin"]), Lines(["end"]))

    def generate_verilog(self, indent: int = 0):
        """
        Generates the verilog (does the most work, calls other functions)
        """
        stmt_lines = self.parse_statements(
            self.root.body, prefix="", end_stmts=Lines(["_done = 1;"])
        )
        module_lines = self.stringify_module()
        decl_lines = self.stringify_declarations(self.global_vars)
        always_blk_lines = self.stringify_always_block()
        decl_and_always_blk_lines = (
            decl_lines[0].concat(always_blk_lines[0]),
            decl_lines[1].concat(always_blk_lines[1]),
        )  # TODO: there should be a function for this
        init_lines = self.stringify_initialization(self.global_vars)

        return Lines.nestify(
            [
                module_lines,
                decl_and_always_blk_lines,
                init_lines,
                stmt_lines,
            ],
            indent,
        )

    @staticmethod
    def stringify_initialization(global_vars: dict[str, str]):
        """
        if (_start) begin
            <var> = <value>;
            ...
        end else begin
        ...
        end
        """
        start_lines, end_lines = Lines(), Lines()
        start_lines += "if (_start) begin"
        start_lines += Indent(1) + "_done <= 0;"
        for var in global_vars:
            start_lines += Indent(1) + f"{var} <= {global_vars[var]};"
        start_lines += "end else begin"
        end_lines += "end"
        return (start_lines, end_lines)

    @staticmethod
    def stringify_declarations(global_vars: dict[str, str]) -> tuple[Lines, Lines]:
        """
        reg [31:0] <name>;
        ...
        """
        return (Lines([f"reg signed [31:0] {v};" for v in global_vars]), Lines())

    def stringify_module(self) -> tuple[Lines, Lines]:
        """
        module <name>(...);

        endmodule
        """
        start_lines, end_lines = Lines(), Lines()
        assert self.name not in {
            "default",
            "module",
            "output",
            "function",
        }  # Verilog Reserved Keywords
        start_lines += f"module {self.name}("
        start_lines += Indent(1) + "input wire _clock,"
        start_lines += Indent(1) + "input wire _start,"
        for var in self.root.args.args:
            start_lines += Indent(1) + f"input wire signed [31:0] {var.arg},"
        for var in self.yield_vars:
            start_lines += Indent(1) + f"output reg signed [31:0] {var},"
        start_lines += Indent(1) + "output reg _done"
        start_lines += ");"
        end_lines += "endmodule"
        return (start_lines, end_lines)

    def __init__(self, root: ast.FunctionDef):
        """
        Initializes the parser, does quick setup work
        """
        self.name = root.name
        self.yield_vars = self.generate_return_vars(root.returns, "")
        self.unique_name_counter = 0
        self.global_vars: dict[str, str] = {}
        self.root = root

    def parse_for(self, node: ast.For, prefix: str = ""):
        """
        Creates a conditional while loop from for loop
        """

        def parse_iter(iterator: ast.AST, node: ast.AST):
            assert isinstance(iterator, ast.Call)
            assert iterator.func.id == "range"

            # range(x, y) or range(x)
            if len(iterator.args) == 2:
                start, end = str(iterator.args[0].value), iterator.args[1].id
            else:
                start, end = "0", iterator.args[0].id

            self.add_global_var(
                start, node.target.id
            )  # TODO: not require unique range iterator variables
            return (
                Lines(
                    [
                        f"if ({node.target.id} >= {end}) begin // FOR LOOP START",
                        Indent(1) + f"{prefix}_STATE = {prefix}_STATE + 1;",
                        Indent(1) + f"{node.target.id} <= 0;",
                        "end else begin // FOR LOOP BODY",
                    ]
                ),
                Lines(["end // FOR LOOP END"]),
            )

        conditional_lines = parse_iter(node.iter, node)
        stmt_lines = self.parse_statements(
            node.body,
            f"{prefix}_BODY_{self.create_unique_name()}",
            end_stmts=Lines([f"{node.target.id} <= {node.target.id} + 1;"]),
            reset_to_zero=True,
        )
        return Lines.nestify([conditional_lines, stmt_lines])

    def parse_targets(self, nodes: list[ast.AST]):
        """
        Warning: only single target on left-hand-side supported

        <target0, target1, ...> =
        """
        buffer = ""
        assert len(nodes) == 1
        for node in nodes:
            assert isinstance(node, ast.Name)
            if node.id not in self.global_vars:
                self.add_global_var(0, node.id)
            buffer += self.parse_expression(node)
        return buffer

    def parse_assign(self, node: ast.Assign):
        """
        <target0, target1, ...> = <value>;
        """
        return f"{self.parse_targets(node.targets)} <= {self.parse_expression(node.value)};"

    def parse_statement(self, stmt: ast.AST, prefix: str = ""):
        """
        <statement> (e.g. assign, for loop, etc., those that do not return a value)
        """
        if isinstance(stmt, ast.Assign):
            return Lines([self.parse_assign(stmt)])
        if isinstance(stmt, ast.For):
            return self.parse_for(stmt, prefix=prefix)
        if isinstance(stmt, ast.Expr):
            return self.parse_statement(stmt.value, prefix=prefix)
        if isinstance(stmt, ast.Yield):
            return self.parse_yield(stmt)
        if isinstance(stmt, ast.While):
            return self.parse_while(stmt, prefix=prefix)
        if isinstance(stmt, ast.If):
            return self.parse_if(stmt, prefix=prefix)
        raise TypeError("Error: unexpected statement type", type(stmt), ast.dump(stmt))

    def parse_if(self, stmt: ast.If, prefix: str = ""):
        """
        If statement
        """
        assert len(stmt.orelse) >= 1  # Currently only supports if-else
        state_var = self.add_global_var("0", f"{prefix}_IF")
        lines = Lines()
        lines += f"case ({state_var}) // IF START"

        state_conditional = self.add_global_var(0, f"{state_var}_CONDITIONAL")
        state_then = self.add_global_var(1, f"{state_var}_THEN")
        state_else = self.add_global_var(2, f"{state_var}_ELSE")

        # If condition
        wrapper = (Lines([f"{state_conditional}: begin"]), Lines(["end"]))
        body = (
            Lines(
                [
                    f"if ({self.parse_expression(stmt.test)}) {state_var} <= {state_then};"
                ]
            ),
            Lines([f"else {state_var} <= {state_else};"]),
        )
        if_condition = Lines.nestify((wrapper, body))

        # If then
        wrapper = (Lines([f"{state_then}: begin"]), Lines(["end"]))
        body = self.parse_statements(
            stmt.body,
            f"{state_var}_{self.create_unique_name()}",
            end_stmts=Lines(
                [
                    f"{prefix}_STATE <= {prefix}_STATE + 1; {state_var} <= {state_conditional};",
                ]
            ),
            reset_to_zero=True,
        )
        if_then = Lines.nestify((wrapper, body))

        # If else
        wrapper = (Lines([f"{state_else}: begin"]), Lines(["end"]))
        body = self.parse_statements(
            stmt.orelse,
            f"{state_var}_{self.create_unique_name()}",
            end_stmts=Lines(
                [
                    f"{prefix}_STATE <= {prefix}_STATE + 1; {state_var} <= {state_conditional};",
                ]
            ),
            reset_to_zero=True,
        )
        if_else = Lines.nestify((wrapper, body))

        lines.concat(if_condition, 1).concat(if_then, 1).concat(if_else, 1)
        lines += "endcase // IF END"
        return lines

    def parse_statements(
        self,
        stmts: list[ast.AST],
        prefix: str,
        end_stmts: Lines = Lines(),
        reset_to_zero: bool = False,
    ):
        """
        Warning: mutates global_vars
        {
            <statement0>
            <statement1>
            ...
        }
        """
        state_var = self.add_global_var("0", f"{prefix}_STATE")
        lines = Lines()
        lines += f"case ({state_var}) // STATEMENTS START"
        previous_i = 0

        for i, stmt in enumerate(stmts):
            state = self.add_global_var(str(i), f"{prefix}_STATE_{i}")

            lines += Indent(1) + f"{state}: begin"

            for line in self.parse_statement(stmt, prefix=prefix).indent(2):
                lines += line
                assert str(line).find("\n") == -1
            if (
                not isinstance(stmt, ast.For)
                and not isinstance(stmt, ast.While)
                and not isinstance(stmt, ast.If)
            ):
                # Non-for-loop state machines always continue to next state
                # after running current state's case statement.
                # TODO: figure out better way to handle this,
                # perhaps add to end statements of caller
                lines += (
                    Indent(2) + f"{state_var} <= {state_var} + 1; // INCREMENT STATE"
                )
            lines += Indent(1) + "end"
            previous_i = i

        assert isinstance(end_stmts, Lines)
        # TODO: cleanup, remove the above enumerate?
        i = previous_i + 1
        # TODO: endStatements should take in array of Lines,
        # where each element in array is one additional case
        for stmt in end_stmts:
            state = self.add_global_var(str(i), f"{prefix}_STATE_{i}")

            lines += Indent(1) + f"{state}: begin // END STATEMENTS STATE"
            lines += Indent(2) + stmt
            lines += Indent(1) + "end"
            i += 1

        del lines[-1]

        if reset_to_zero:  # TODO: think about what default should be
            lines += Indent(2) + f"{state_var} <= 0; // LOOP FOR LOOP STATEMENTS"

        lines += Indent(1) + "end"

        lines += "endcase // STATEMENTS END"
        return (lines, Lines())

    def parse_yield(self, node: ast.Yield):
        """
        Warning: may not work for single output

        Warning: requires self.yieldVars to be complete

        yield <value>;
        """
        assert isinstance(node.value, ast.Tuple)
        lines = Lines()
        for idx, elem in enumerate(node.value.elts):
            lines += f"{self.yield_vars[idx]} <= {self.parse_expression(elem)};"
        return lines

    @staticmethod
    def parse_binop(node: ast.BinOp):
        """
        <left> <op> <right>
        """
        if isinstance(node.op, ast.Add):
            return " + "
        if isinstance(node.op, ast.Sub):
            return " - "
        if isinstance(node.op, ast.Mult):
            return " * "
        if isinstance(node.op, ast.Div):
            return " / "
        raise TypeError(
            "Error: unexpected binop type", type(node.op), ast.dump(node.op)
        )

    def parse_expression(self, expr: ast.AST):
        """
        <expression> (e.g. constant, name, subscript, etc., those that return a value)
        """
        if isinstance(expr, ast.Constant):
            return str(expr.value)
        if isinstance(expr, ast.Name):
            return expr.id
        if isinstance(expr, ast.Subscript):
            return self.parse_subscript(expr)
        if isinstance(expr, ast.BinOp):
            return (
                "("
                + self.parse_expression(expr.left)
                + self.parse_binop(expr)
                + self.parse_expression(expr.right)
                + ")"
            )
        if isinstance(expr, ast.Compare):
            return self.parse_compare(expr)
        raise TypeError("Error: unexpected expression type", type(expr))

    def parse_subscript(self, node: ast.Subscript):
        """
        <value>[<slice>]
        Note: built from right to left, e.g. [z] -> [y][z] -> [x][y][z] -> matrix[x][y][z]
        """
        return (
            f"{self.parse_expression(node.value)}[{self.parse_expression(node.slice)}]"
        )

    def parse_compare(self, node: ast.Compare):
        """
        <left> <op> <comparators>
        """
        assert len(node.ops) == 1
        assert len(node.comparators) == 1

        if isinstance(node.ops[0], ast.Lt):
            operator = "<"
        elif isinstance(node.ops[0], ast.LtE):
            operator = "<="
        elif isinstance(node.ops[0], ast.Gt):
            operator = ">"
        elif isinstance(node.ops[0], ast.GtE):
            operator = ">="
        else:
            raise TypeError(
                "Error: unknown operator", type(node.ops[0]), ast.dump(node.ops[0])
            )
        return f"{self.parse_expression(node.left)} {operator} \
            {self.parse_expression(node.comparators[0])}"

    def parse_while(self, node: ast.While, prefix: str = ""):
        """
        Converts while loop to a while-true-if-break loop
        """
        conditional = (
            Lines(
                [
                    f"if (!({self.parse_expression(node.test)})) begin // WHILE LOOP START",
                    Indent(1) + f"{prefix}_STATE = {prefix}_STATE + 1;",
                    "end else begin",
                ]
            ),
            Lines(["end // WHILE LOOP END"]),
        )

        statements = self.parse_statements(
            node.body, f"{prefix}_BODY_{self.create_unique_name()}", reset_to_zero=True
        )

        return Lines.nestify([conditional, statements])
