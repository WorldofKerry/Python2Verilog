"""
Intermediate Representation Expressions
Based on Verilog Syntax
"""


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
