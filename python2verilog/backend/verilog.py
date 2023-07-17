"""Verilog Abstract Syntax Tree Components"""

import warnings
import ast

from ..utils.string import Lines, Indent
from ..utils.assertions import assert_list_elements
from .. import ir as irast


class Expression:
    """
    Verilog expression, e.g.
    a + b
    Currently just a string
    """

    def __init__(self, expr: str):
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


class Statement:
    """
    Represents a statement in verilog (i.e. a line or a block)
    If used directly, it is treated as a string literal
    """

    def __init__(self, literal: str = None, comment: str = ""):
        self.literal = literal
        self.comment = comment

    def to_lines(self):
        """
        To Verilog
        """
        return Lines(self.literal + self.get_inline_comment())

    def to_string(self):
        """
        To Verilog
        """
        return self.to_lines().to_string()

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


class Verilog:
    """
    Code Generation for Verilog
    """

    def create_module_from_python(self, func: ast.FunctionDef):
        """
        Creates a module wrapper from python AST,
        e.g. the I/O (from Python), clock, valid and done signals
        """
        inputs = []
        for var in func.args.args:
            inputs.append(var.arg)
        outputs = []
        assert isinstance(func.returns, ast.Subscript)
        assert isinstance(func.returns.slice, ast.Tuple)
        for i in range(len((func.returns.slice.elts))):
            outputs.append(f"_out{str(i)}")
        # TODO: make these extras optional
        return Module(func.name, inputs, outputs, body=[self.always])

    def __init__(self):
        # TODO: throw errors if user tries to generate verilog beforeconfig
        self.root = None
        self.global_vars = None
        self.module = None
        self.always = None
        self.python_func = None

    def build_tree(self, node: irast.Statement):
        """
        Builds the Verilog AST
        """
        if not node:
            return Statement("")
        if isinstance(node, irast.Case):
            case_items = []
            for item in node.case_items:
                case_items.append(self.build_tree(item))
            return Case(self.build_tree(node.condition), case_items)
        if isinstance(node, irast.CaseItem):
            case_items = []
            for item in node.statements:
                case_items.append(self.build_tree(item))
            return CaseItem(self.build_tree(node.condition), case_items)
        if isinstance(node, irast.Expression):
            return Expression(node.to_string())
        return Statement(node.to_string().replace("\n", " "))

    def from_ir(self, root: irast.Statement, global_vars: dict[str, str]):
        """
        Builds tree from IR
        """
        root.append_end_statements([irast.NonBlockingSubsitution("_done", "1")])
        self.root = self.build_tree(root)
        self.global_vars = global_vars
        return self

    def get_init(self, global_vars: dict[str, str]):
        """
        if (_start) begin
            <var> = <value>;
            ...
        end else begin
        ...
        end
        """
        then_body = [NonBlockingSubsitution("_done", "0")] + [
            NonBlockingSubsitution(key, str(val)) for key, val in global_vars.items()
        ]
        block = IfElse(
            Expression("_start"),
            then_body,
            [self.root],
        )
        return block

    def get_module(self):
        """
        Get Verilog module
        """
        decls = [Declaration(v, is_reg=True, is_signed=True) for v in self.global_vars]
        self.module.body = decls + self.module.body
        return self.module.to_lines()

    def setup_from_python(self, func: ast.FunctionDef):
        """
        Setups up module, always block, declarations, etc from Python AST
        """
        assert self.global_vars is not None, "run from_ir first to setup global_vars"
        assert isinstance(func, ast.FunctionDef)
        self.always = PosedgeSyncAlways(
            Expression("_clock"), valid="_valid", body=[self.get_init(self.global_vars)]
        )
        self.module = self.create_module_from_python(func)
        self.python_func = func
        return self

    def get_testbench(self, test_case: tuple):
        """
        Creates a test bench for a test case
        TODO: convert output to lines
        """
        func = self.python_func
        func_name = func.name

        text = f"module {func_name}"

        text += """_tb;
    // Inputs
    reg _clock;
    reg _start;
    """  # TODO: use the NAMED_FUNCTION constant instead of generator
        for idx, val in enumerate(func.args.args):
            text += f"  reg signed [31:0] {val.arg};\n"
        text += "\n  // Outputs\n"
        for idx in range(len(func.returns.slice.elts)):
            text += f"  wire signed [31:0] _out{idx};\n"

        text += """
    wire _done;
    wire _valid;

    // Instantiate the module under test
    """
        text += func_name

        text += """ dut (
    ._clock(_clock),
    ._start(_start),
    """
        for idx, val in enumerate(func.args.args):
            text += f"    .{val.arg}({val.arg}),\n"
        for idx in range(len(func.returns.slice.elts)):
            text += f"    ._out{idx}(_out{idx}),\n"
        text += """
    ._done(_done),
    ._valid(_valid)
    );

    // Clock generation
    always #5 _clock = !_clock;

    // Stimulus
    initial begin
    // Initialize inputs
    _start = 0;
    """

        for idx, val in enumerate(func.args.args):
            text += f"    {val.arg} = {test_case[idx]};\n"
        text += """
    _clock = 0;

    // Wait for a few clock cycles
    #10;

    // Start the drawing process
    @(posedge _clock);
    _start = 1;
    @(posedge _clock);

    // Wait for the drawing to complete
    while (!_done) begin
    @(posedge _clock);
    _start = 0;
    // Display the outputs for every cycle after start
    $display(\"%0d, """  # TODO: use NAMED_FUNCTION instead of "generator dut"

        text += "%0d, " * (len(func.returns.slice.elts) - 1)
        text += """%0d\", _valid"""

        for idx in range(len(func.returns.slice.elts)):
            text += f", _out{idx}"

        text += ");\n"

        text += """
    end

    // Finish simulation
    $finish;
    end

    endmodule
    """
        return text

    def get_testbench_improved(self, test_cases: list[tuple[str]]):
        """
        Creates testbench with multiple test cases using the _done signal
        """

        def make_display_stmt(func: ast.FunctionDef):
            string = '$display("%0d, '
            string += "%0d, " * (len(func.returns.slice.elts) - 1)
            string += '%0d", _valid'
            for i in range(len(func.returns.slice.elts)):
                string += f", _out{i}"
            string += ");"
            return Statement(literal=string)

        setups = []
        setups.append(Declaration("_clock", size=1, is_reg=True))
        setups.append(Declaration("_start", size=1, is_reg=True))

        func = self.python_func

        setups += [
            Declaration(val.arg, is_signed=True, is_reg=True) for val in func.args.args
        ]
        setups += [
            Declaration(f"_out{idx}", is_signed=True)
            for idx in range(len(func.returns.slice.elts))
        ]

        setups.append(Declaration("_done", size=1))
        setups.append(Declaration("_valid", size=1))

        ports = {
            decl.name: decl.name for decl in setups
        }  # Caution: expects setups to only contain declarations
        setups.append(Instantiation(func.name, "DUT", ports))

        setups.append(Statement(literal="always #5 _clock = !_clock;"))

        initial_body = []
        initial_body.append(BlockingSubsitution("_clock", "0"))
        initial_body.append(BlockingSubsitution("_start", "0"))
        initial_body.append(AtPosedgeStatement(Expression("_clock")))
        initial_body.append(AtPosedgeStatement(Expression("_clock")))

        for test_case in test_cases:
            # setup for new test case
            for i, var in enumerate(func.args.args):
                initial_body.append(BlockingSubsitution(var.arg, str(test_case[i])))
            initial_body.append(BlockingSubsitution("_start", "1"))

            initial_body.append(AtPosedgeStatement(Expression("_clock")))
            initial_body.append(AtPosedgeStatement(Expression("_clock")))

            # wait for done signal
            while_body = []
            while_body.append(AtPosedgeStatement(Expression("_clock")))
            while_body.append(BlockingSubsitution("_start", "0"))
            while_body.append(make_display_stmt(func))

            initial_body.append(While(condition=Expression("!_done"), body=while_body))

        initial_body.append(Statement(literal="$finish;"))

        initial_loop = Initial(body=initial_body)

        module = Module(
            f"{func.name}_tb",
            [],
            [],
            body=setups + [initial_loop],
            add_default_ports=False,
        )
        return module


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


class Module:
    """
    module name(...); endmodule
    """

    def __init__(
        self,
        name: str,
        inputs: list[str],
        outputs: list[str],
        body: list[Statement] = None,
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

    def __init__(self, *args, body: list[Statement] = None, **kwargs):
        if body:
            assert_list_elements(body, Statement)
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
        body: list[Statement] = None,
        valid: str = "",
        **kwargs,
    ):
        assert isinstance(trigger, Expression)
        self.trigger = trigger
        if valid != "":
            valid = NonBlockingSubsitution(valid, "0")
        self.valid = valid
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
        if self.valid != "":
            lines.concat(self.valid.to_lines(), 1)
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

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        assert isinstance(
            rvalue, str
        ), f"got {type(rvalue)} instead"  # TODO: should eventually take an expression
        assert isinstance(lvalue, str)
        self.lvalue = lvalue
        self.rvalue = rvalue
        self.type = None
        self.appended = []
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        Converts to Verilog
        """
        assert isinstance(self.type, str), "Subclasses need to set self.type"
        itself = f"{self.lvalue} {self.type} {self.rvalue};"
        lines = Lines(itself)
        if self.appended:
            for stmt in self.appended:
                lines.concat(stmt.to_lines())
        return lines

    def append_end_statements(self, statements: list[Statement]):
        """
        Appends to last block of code
        """
        self.appended = self.appended + assert_list_elements(statements, Statement)
        return self


class NonBlockingSubsitution(Subsitution):
    """
    <lvalue> <= <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        super().__init__(lvalue, rvalue, *args, **kwargs)
        self.type = "<="


class BlockingSubsitution(Subsitution):
    """
    <lvalue> = <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        super().__init__(lvalue, rvalue, *args, *kwargs)
        self.type = "="


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

    def append_end_statements(self, statements: list[Statement]):
        """
        Append statements to case item
        """
        # self.statements = self.statements + assert_list_elements(statements, Statement)
        # warnings.warn(statements[0].to_string() + " " + str(type(self.statements[-1])))
        self.statements[-1].append_end_statements(
            assert_list_elements(statements, Statement)
        )
        # warnings.warn(statements[0].to_string())
        return self


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

    def append_end_statements(self, statements: list[Statement]):
        """
        Adds statements to the last case item
        """
        self.case_items[-1].append_end_statements(
            assert_list_elements(statements, Statement)
        )
        return self


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
        self.condition = condition
        self.then_body = assert_list_elements(then_body, Statement)
        self.else_body = assert_list_elements(else_body, Statement)

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
        statements = assert_list_elements(statements, Statement)
        # warnings.warn("appending " + statements[0].to_string())
        # if len(statements) > 1:
        #     warnings.warn(statements[1].to_string())
        self.then_body[-1].append_end_statements(statements)
        self.else_body[-1].append_end_statements(statements)
        return self


class WhileCase(Case):
    """
    Abstract While wrapper that is synthesizable
    Case (WHILE)
        0: if (!<conditional>)
                <continue>
            else
                <loop body / go state 1>
        1: <loop body>
    """

    def append_end_statements(self, statements: list[Statement]):
        """
        While statements have a special case structure,
        where their first case always contains an if statement
        """
        statements = assert_list_elements(statements, Statement)
        assert isinstance(self.case_items[0], CaseItem)
        assert isinstance(self.case_items[0].statements[0], IfElse)
        self.case_items[0].statements[0].then_body = (
            self.case_items[0].statements[0].then_body + statements
        )
        return self


class While(Statement):
    """
    Unsynthesizable While
    while (<condition>) begin
        ...
    end
    """

    def __init__(
        self, *args, condition: Expression, body: list[Statement] = None, **kwargs
    ):
        assert isinstance(condition, Expression)
        self.condition = condition
        if body:
            assert_list_elements(body, Statement)
        self.body = body
        super().__init__(*args, **kwargs)

    def to_lines(self):
        lines = Lines(f"while ({self.condition.to_string()}) begin")
        for stmt in self.body:
            lines.concat(stmt.to_lines(), 1)
        lines += "end"
        return lines
