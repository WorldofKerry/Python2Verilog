from python2verilog.ir.statements import (
    NonBlockingSubsitution,
    BlockingSubsitution,
    Declaration,
    Case,
    CaseItem,
)
from python2verilog.ir.expressions import Expression
from python2verilog import ir


import unittest
import warnings


class TestAst(unittest.TestCase):
    def assert_lines(self, first: str, second: str):
        """
        Asserts that each stripped line in first matches each stripped line in second
        """
        self.assertTrue(isinstance(first, str) and isinstance(second, str))
        for a_line, b_line in zip(first.splitlines(), second.splitlines()):
            self.assertEqual(a_line.strip(), b_line.strip())

    # def test_comments(self):
    #     nb = NonBlockingSubsitution("a", "b", comment="ayo")
    #     self.assertEqual(nb.to_string(), "a <= b; // ayo")

    def test_subsitution(self):
        nb = NonBlockingSubsitution(ir.Var("a"), ir.Var("b"))
        self.assertEqual(nb.to_string(), "a <= b;\n")

        b = BlockingSubsitution(ir.Var("c"), ir.Var("d"))
        self.assertEqual(b.to_string(), "c = d;\n")

    def test_declaration(self):
        decl = Declaration("name")
        self.assertEqual(decl.to_string(), "wire [31:0] name;\n")

        decl = Declaration("name", size=64, is_reg=True, is_signed=True)
        self.assertEqual(decl.to_string(), "reg signed [63:0] name;\n")

    def test_case(self):
        item0 = CaseItem(Expression("0"), [BlockingSubsitution(ir.Var("a"), ir.Int(0))])
        item1 = CaseItem(Expression("1"), [BlockingSubsitution(ir.Var("b"), ir.Int(1))])
        case = Case(Expression("cur_state"), [item0, item1])
        self.assert_lines(
            case.to_string(),
            "case (cur_state) \n 0: begin \n a = 0; \n end \n 1: begin \n b = 1; \n end \n endcase",
        )
