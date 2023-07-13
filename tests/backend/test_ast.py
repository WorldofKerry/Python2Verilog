from python2verilog.backend.ast import (
    NonBlockingSubsitution,
    BlockingSubsitution,
    Declaration,
)
import unittest
import warnings


class TestAST(unittest.TestCase):
    def test_comments(self):
        nb = NonBlockingSubsitution("a", "b", comment="ayo")
        self.assertEqual(nb.to_string(), "a <= b; // ayo")

    def test_subsitution(self):
        nb = NonBlockingSubsitution("a", "b")
        self.assertEqual(nb.to_string(), "a <= b;")

        b = BlockingSubsitution("c", "d")
        self.assertEqual(b.to_string(), "c = d;")

    def test_declaration(self):
        decl = Declaration("name")
        self.assertEqual(decl.to_string(), "wire [31:0] name;")

        decl = Declaration("name", size=64, is_reg=True, is_signed=True)
        self.assertEqual(decl.to_string(), "reg signed [63:0] name;")
