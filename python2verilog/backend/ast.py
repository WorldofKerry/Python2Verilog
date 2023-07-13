"""Verilog Abstract Syntax Tree Components"""


class VerilogStmt:
    """
    Represents a statement in verilog (i.e. a line or a block)
    """

    def to_string(self) -> str:
        """
        Gets string representation of Verilog statement
        """
        raise NotImplementedError("Interface has no to_string")


class Subsitution(VerilogStmt):
    """
    Interface for
    <lvalue> <blocking or nonblocking> <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str):
        self.lvalue = lvalue
        self.rvalue = rvalue
        self.type = None

    def to_string(self) -> str:
        """
        Converts to Verilog
        """
        assert isinstance(self.type, str)
        return f"{self.lvalue} {self.type} {self.rvalue};"


class NonBlockingSubsitution(Subsitution):
    """
    <lvalue> <= <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str):
        super().__init__(lvalue, rvalue)
        self.type = "<="


class BlockingSubsitution(Subsitution):
    """
    <lvalue> = <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str):
        super().__init__(lvalue, rvalue)
        self.type = "="


class Declaration(VerilogStmt):
    """
    <reg or wire> <modifiers> <[size-1:0]> <name>;
    """

    def __init__(
        self, name: str, size: int = 32, is_reg: bool = False, is_signed: bool = False
    ):
        self.size = size
        self.is_reg = is_reg
        self.is_signed = is_signed
        self.name = name

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
