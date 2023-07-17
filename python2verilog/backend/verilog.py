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

    def __init__(self, string: str):
        self.string = string

    def to_string(self):
        """
        To Verilog
        """
        return self.string


class Statement:
    """
    Represents a statement in verilog (i.e. a line or a block)
    If used directly, it is treated as a string literal
    """

    def __init__(self, literal: str = None):
        self.literal = literal

    def to_lines(self):
        """
        To Verilog
        """
        return Lines(self.literal)

    def to_string(self):
        """
        To Verilog
        """
        return self.to_lines().to_string()

    # def append_end_statements(self, statements: list):
    #     warnings.warn("append_end_statements on base class")
    #     self.literal += str(statements)


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
        # start_lines, end_lines = Lines(), Lines()
        # start_lines += "if (_start) begin"
        # start_lines += Indent(1) + "_done <= 0;"
        # for var in global_vars:
        #     start_lines += Indent(1) + f"{var} <= {global_vars[var]};"
        # start_lines += "end else begin"
        # end_lines += "end"
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
            "_clock", valid="_valid", body=[self.get_init(self.global_vars)]
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


class Instantiation:
    """
    Instantiationo f Verilog module.
    <given-name> <module-name> (...);
    """

    def __init__(
        self, given_name: str, module_name: str, port_connections: dict[str, str]
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

    def to_lines(self):
        """
        To Verilog
        """
        lines = Lines()
        lines += f"{self.given_name} {self.module_name} ("
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
    ):
        self.name = name  # TODO: assert invalid names

        input_lines = Lines()
        for inputt in inputs:
            assert isinstance(inputt, str)
            input_lines += f"input wire [31:0] {inputt}"
        input_lines += "input wire _start"
        input_lines += "input wire _clock"
        self.input = input_lines

        output_lines = Lines()
        for output in outputs:
            assert isinstance(output, str)
            output_lines += f"output reg [31:0] {output}"
        output_lines += "output reg _done"
        output_lines += "output reg _valid"
        self.output = output_lines

        if body:
            for stmt in body:
                assert isinstance(stmt, Statement)
            self.body = body
        else:
            self.body = []

    def to_lines(self):
        """
        To Verilog
        """
        lines = Lines()
        lines += f"module {self.name}("
        for line in self.input:
            lines += Indent(1) + line + ","
        for line in self.output:
            lines += Indent(1) + line + ","
        lines[-1] = lines[-1][0:-1]  # removes last comma
        lines += ");"
        for stmt in self.body:
            lines.concat(stmt.to_lines(), 1)
        lines += "endmodule"
        return lines


class Initial(Statement):
    """
    initial begin
        ...
    end
    """


class Always(Statement):
    """
    always () begin
        ...
    end
    """

    def __init__(
        self,
        trigger: str,
        *args,
        body: list[Statement] = None,
        valid: str = "",
        **kwargs,
    ):
        assert isinstance(trigger, str)
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
        lines = Lines(f"always {self.trigger} begin")
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

    def __init__(self, clock: str, *args, **kwargs):
        assert isinstance(clock, str)
        self.clock = clock
        super().__init__(f"@(posedge {self.clock})", *args, **kwargs)


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


class While(Case):
    """
    Abstract While wrapper
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
