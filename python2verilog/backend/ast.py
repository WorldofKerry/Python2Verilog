"""Verilog Abstract Syntax Tree Components"""


class Subsitution:
    """
    Interface for
    <lvalue> <blocking or nonblocking> <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str):
        self.lvalue = lvalue
        self.rvalue = rvalue

    def to_string(self) -> str:
        assert isinstance(self.type, str)
        return f"{self.lvalue} {self.type} {self.rvalue};"


class NonBlockingSubsitution(Subsitution):
    """
    <lvalue> <= <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str):
        super().__init__(lvalue, rvalue)
        self.type = "<="

    def to_string(self) -> str:
        return super().to_string()
