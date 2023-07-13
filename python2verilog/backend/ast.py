"""Verilog Abstract Syntax Tree Components"""

from ..frontend.utils import Indent, Lines


class Expression:
    """
    Verilog expression, e.g.
    a + b
    Currently just a string
    """

    def __init__(self, string: str):
        self.string = string

    def to_lines(self):
        return self.string


class Statement:
    """
    Represents a statement in verilog (i.e. a line or a block)
    """

    def __init__(self, comment: str = None):
        self.comment = comment

    def to_string(self):
        return self.to_lines().to_string()


class Subsitution(Statement):
    """
    Interface for
    <lvalue> <blocking or nonblocking> <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        self.lvalue = lvalue
        self.rvalue = rvalue
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        Converts to Verilog
        """
        assert isinstance(self.type, str), "Subclasses need to set self.type"
        return Lines(f"{self.lvalue} {self.type} {self.rvalue};")


class NonBlockingSubsitution(Subsitution):
    """
    <lvalue> <= <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        self.type = "<="
        super().__init__(lvalue, rvalue, *args, **kwargs)


class BlockingSubsitution(Subsitution):
    """
    <lvalue> = <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        self.type = "="
        super().__init__(lvalue, rvalue, *args, *kwargs)


class Declaration(Statement):
    """
    <reg or wire> <modifiers> <[size-1:0]> <name>;
    """

    def __init__(
        self,
        name: str,
        size: int = 32,
        is_reg: bool = False,
        is_signed: bool = False,
        *args,
        **kwargs,
    ):
        self.size = size
        self.is_reg = is_reg
        self.is_signed = is_signed
        self.name = name
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        To Verilog
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


class Case(Statement):
    """
    Verilog case statement with various cases
    case (<condition>)
        ...
    endcase
    """

    def __init__(self, condition: Expression, items: list[CaseItem], *args, **kwargs):
        self.condition = condition
        if items:
            for item in item:
                assert isinstance(item, CaseItem)
            self.items = items
        else:
            items = []
        super().__init__(*args, **kwargs)

    def to_lines(self):
        lines = Lines()
        lines += f"case ({self.condition.to_lines()})"
        for item in self.items:
            lines.concat(item, indent=1)
        return lines
