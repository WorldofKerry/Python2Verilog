"""
Verilog Abstract Syntax Tree Components
"""

from __future__ import annotations

import itertools
from typing import Optional

from ... import ir
from ...utils.assertions import assert_typed_dict, get_typed, get_typed_list
from ...utils.string import ImplementsToLines, Indent, Lines


class AtPosedge(ir.Expression):
    """
    @(posedge <condition>)
    """

    def __init__(self, condition: ir.Expression):
        assert isinstance(condition, ir.Expression)
        self.condition = condition
        super().__init__(f"@(posedge {condition.to_string()})")


class AtNegedge(ir.Expression):
    """
    @(negedge <condition>)
    """

    def __init__(self, condition: ir.Expression):
        assert isinstance(condition, ir.Expression)
        self.condition = condition
        super().__init__(f"@(negedge {condition.to_string()})")


class Statement(ImplementsToLines):
    """
    Represents a statement in verilog (i.e. a line or a block)
    If used directly, it is treated as a string literal
    """

    def __init__(self, literal: str = "", comment: str = ""):
        self.literal = get_typed(literal, str)
        self.comment = get_typed(comment, str)

    def to_lines(self):
        """
        To Verilog
        """
        if self.literal:
            return Lines(self.literal + self.get_inline_comment())
        return Lines(self.get_inline_comment()[1:])  # removes leading space

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


class LocalParam(Statement):
    """
    localparam <name> = <value>;
    """

    def __init__(self, name: ir.Expression, value: ir.UInt, *args, **kwargs):
        assert isinstance(value, ir.UInt)
        super().__init__(f"localparam {name} = {value};", *args, **kwargs)


class AtPosedgeStatement(Statement):
    """
    @(posedge <condition>);
    """

    def __init__(self, condition: ir.Expression, *args, **kwargs):
        assert isinstance(condition, ir.Expression)
        super().__init__(f"{AtPosedge(condition).to_string()};", *args, **kwargs)


class AtNegedgeStatement(Statement):
    """
    @(negedge <condition>);
    """

    def __init__(self, condition: ir.Expression, *args, **kwargs):
        assert isinstance(condition, ir.Expression)
        super().__init__(f"{AtNegedge(condition).to_string()};", *args, **kwargs)


class Instantiation(Statement):
    """
    Instantiationo f Verilog module.
    <module-name> <given-name> (...);
    """

    def __init__(
        self,
        module_name: str,
        given_name: str,
        port_connections: dict[ir.Expression | str, ir.Expression | str],
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
        is_not_testbench=True,
        localparams: Optional[dict[ir.Expression, ir.UInt]] = None,
        header_comment: Optional[Lines] = None,
    ):
        self.name = name

        input_lines = Lines()
        if is_not_testbench:
            input_lines += "// Function parameters:"
            for input_ in inputs:
                assert isinstance(input_, str)
                input_lines += f"input wire signed [31:0] {input_},"
            input_lines.blank()
            input_lines += "input wire _clock, // clock for sync"
            input_lines += (
                "input wire _reset, // set high to reset, i.e. done will be high"
            )
            input_lines += (
                "input wire _start, "
                + "// set high to capture inputs (in same cycle) and start generating"
            )
            input_lines.blank()
            input_lines += "// Implements a ready/valid handshake based on"
            input_lines += "// http://www.cjdrake.com/readyvalid-protocol-primer.html"
            input_lines += (
                "input wire _ready, // set high when caller is ready for output"
            )
        self.input = input_lines

        output_lines = Lines()
        if is_not_testbench:
            output_lines += "output reg _valid, // is high if output is valid"
            output_lines.blank()
            output_lines += "output reg _done, // is high if module done outputting"
            output_lines.blank()
            output_lines += "// Output values as a tuple with respective index(es)"
            for output in outputs:
                assert isinstance(output, str)
                output_lines += f"output reg signed [31:0] {output},"
        self.output = output_lines

        if body:
            for stmt in body:
                assert isinstance(stmt, Statement), f"got {type(stmt)} instead"
            self.body = body
        else:
            self.body = []

        if localparams:
            assert_typed_dict(localparams, str, ir.UInt)  # type: ignore[misc]
            self.local_params = Lines()
            for key, value in localparams.items():
                self.local_params.concat(LocalParam(key, value).to_lines())
        else:
            self.local_params = Lines()

        self.header_comment = header_comment

    def to_lines(self):
        """
        To Verilog
        """
        if self.header_comment:
            lines = Lines(self.header_comment.lines)
        else:
            lines = Lines()
        lines += f"module {self.name} ("
        for line in self.input:
            lines += Indent(1) + line
        for line in self.output:
            lines += Indent(1) + line
        if len(lines) > 1:  # This means there are ports
            lines[-1] = lines[-1][0:-1]  # removes last comma
        lines += ");"
        lines.concat(self.local_params, 1)
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

    def __init__(self, *args, body: Optional[list[Statement]] = None, **kwargs):
        if body:
            get_typed_list(body, Statement)
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
        trigger: ir.Expression,
        *args,
        body: Optional[list[Statement]] = None,
        **kwargs,
    ):
        assert isinstance(trigger, ir.Expression)
        self.trigger = trigger
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

    def __init__(self, clock: ir.Expression, *args, **kwargs):
        assert isinstance(clock, ir.Expression)
        self.clock = clock
        super().__init__(AtPosedge(clock), *args, **kwargs)


class Subsitution(Statement):
    """
    Interface for
    <lvalue> <blocking or nonblocking> <rvalue>
    """

    def __init__(
        self,
        lvalue: ir.Expression,
        rvalue: ir.Expression,
        oper: str,
        *args,
        **kwargs,
    ):
        assert isinstance(rvalue, (ir.Expression)), f"got {type(rvalue)} instead"
        assert isinstance(lvalue, (ir.Expression))
        self.lvalue = lvalue
        self.rvalue = rvalue
        self.oper = oper

        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        Converts to Verilog
        """
        assert isinstance(self.oper, str), "Subclasses need to set self.type"
        self.literal = f"{self.lvalue} {self.oper} {self.rvalue};"
        return super().to_lines()


class NonBlockingSubsitution(Subsitution):
    """
    <lvalue> <= <rvalue>
    """

    def __init__(self, lvalue: ir.Expression, rvalue: ir.Expression, *args, **kwargs):
        super().__init__(lvalue, rvalue, "<=", *args, **kwargs)


class BlockingSub(Subsitution):
    """
    <lvalue> = <rvalue>
    """

    def __init__(self, lvalue: ir.Expression, rvalue: ir.Expression, *args, **kwargs):
        super().__init__(lvalue, rvalue, "=", *args, **kwargs)


class Declaration(Statement):
    """
    <reg or wire> <modifiers> <[size-1:0]> <name>;
    """

    def __init__(
        self,
        name: ir.Expression | str,
        *args,
        size: int = 32,
        reg: bool = False,
        signed: bool = False,
        **kwargs,
    ):
        self.size = size
        self.reg = reg
        self.signed = signed
        self.name = name
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        To Verilog lines
        """
        string = ""
        if self.reg:
            string += "reg"
        else:
            string += "wire"
        if self.signed:
            string += " signed"
        if self.size > 1:
            string += f" [{self.size-1}:0]"
        string += f" {self.name}"
        string += ";"
        return Lines(string)


class CaseItem(ImplementsToLines):
    """
    Verilog case item, i.e.
    <condition>: begin
        <statements>
    end
    """

    def __init__(self, condition: ir.Expression, statements: list[Statement]):
        assert isinstance(condition, ir.Expression)
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
        self, expression: ir.Expression, case_items: list[CaseItem], *args, **kwargs
    ):
        assert isinstance(expression, ir.Expression)
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
        condition: ir.Expression,
        then_body: list[Statement],
        else_body: Optional[list[Statement]],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.condition = get_typed(condition, ir.Expression)
        self.then_body = get_typed_list(then_body, Statement)
        self.else_body = get_typed_list(else_body, Statement)

    def to_lines(self):
        lines = Lines()
        lines += f"if ({self.condition.to_string()}) begin"
        for stmt in self.then_body:
            lines.concat(stmt.to_lines(), indent=1)
        if self.else_body:
            lines += "end else begin"
            for stmt in self.else_body:
                lines.concat(stmt.to_lines(), indent=1)
        lines += "end"
        return lines


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
        condition: ir.Expression,
        body: Optional[list[Statement]] = None,
        **kwargs,
    ):
        assert isinstance(condition, ir.Expression)
        self.condition = condition
        if body:
            get_typed_list(body, Statement)
        self.body = body
        super().__init__(*args, **kwargs)

    def to_lines(self):
        lines = Lines(f"while ({self.condition.to_string()}) begin")
        for stmt in self.body:
            lines.concat(stmt.to_lines(), 1)
        lines += "end"
        return lines
