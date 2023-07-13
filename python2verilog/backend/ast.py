"""Verilog Abstract Syntax Tree Components"""


class VerilogStmt:
    """
    Represents a statement in verilog (i.e. a line or a block)
    """

    def __init__(self, comment: str = None):
        self.comment = comment

    def to_string(self) -> str:
        """
        Gets string representation of Verilog statement
        """
        if self.comment:
            return " // " + self.comment
        return ""


class Subsitution(VerilogStmt):
    """
    Interface for
    <lvalue> <blocking or nonblocking> <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        self.lvalue = lvalue
        self.rvalue = rvalue
        super().__init__(*args, **kwargs)

    def to_string(self) -> str:
        """
        Converts to Verilog
        """
        assert isinstance(self.type, str), "Subclasses need to set self.type"
        return f"{self.lvalue} {self.type} {self.rvalue};" + super().to_string()


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


class Declaration(VerilogStmt):
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

    def to_string(self) -> str:
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
        return string
