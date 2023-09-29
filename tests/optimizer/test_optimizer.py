import logging
import unittest
import warnings

from python2verilog import ir
from python2verilog.backend.verilog import CodeGen
from python2verilog.optimizer.optimizer import backwards_replace


class TestGraphApplyMapping(unittest.TestCase):
    def test_mapping(self):
        a = ir.Var("a")
        b = ir.Var("b")
        c = ir.Var("c")
        zero = ir.Int(0)
        one = ir.Int(1)

        changes = [a, zero], [b, one], [c, zero], [a, b], [b, c], [c, ir.Add(a, b)]
        """
        a = 0
        b = 1
        c = 0
        a = b
        b = c
        c = a + b
        """

        mapping = {}
        for lvalue, rvalue in changes:
            new_rvalue = backwards_replace(rvalue, mapping)
            mapping[lvalue] = new_rvalue

        self.assertEqual(mapping, {a: one, b: zero, c: ir.Add(one, zero)})
        """
        a = 1
        b = 0
        c = 1 + 0
        """
