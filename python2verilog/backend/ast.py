"""Verilog Abstract Syntax Tree Components"""

from enum import Enum


class Subsitution:
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


# class Declaration:
#     """
#     <reg or wire> <modifiers>
#     """

#     def __init__(self, is_reg: bool = False, is_signed: bool = False):
