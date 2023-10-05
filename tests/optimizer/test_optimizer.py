import itertools
import logging
import unittest
import warnings
from typing import Any

from python2verilog import ir
from python2verilog.backend.verilog import CodeGen
from python2verilog.backend.verilog.codegen import CaseBuilder
from python2verilog.optimizer.optimizer import OptimizeGraph, backwards_replace


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

    def test_combine_var(self):
        a = ir.Var("a")
        b = ir.Var("b")
        c = ir.Var("c")

        count_inst = itertools.count()
        ui = lambda: str(next(count_inst))

        head = ir.ClockedEdge(ui())
        node = head
        node.child = ir.AssignNode(ui(), lvalue=a, rvalue=b)
        node = node.child
        node.child = ir.ClockedEdge(ui())
        node = node.child
        node.child = ir.AssignNode(ui(), lvalue=a, rvalue=c)
        node = node.child
        node.child = ir.ClockedEdge(ui())
        node = node.child
        node.child = ir.DoneNode(ui())

        node = OptimizeGraph(head.child).reduce_cycles_visit(head, {}, {}, 1)
        cases = CaseBuilder(head.child, ir.Context()).get_case()
        logging.error(cases.to_string())

    def test_combine_exclusive(self):
        a = ir.ExclusiveVar("a")
        b = ir.ExclusiveVar("b")
        c = ir.ExclusiveVar("c")

        count_inst = itertools.count()
        ui = lambda: str(next(count_inst))

        head = ir.ClockedEdge(ui())
        node = head
        node.child = ir.AssignNode(ui(), lvalue=a, rvalue=b)
        node = node.child
        node.child = ir.ClockedEdge(ui())
        node = node.child
        node.child = ir.AssignNode(ui(), lvalue=a, rvalue=c)
        node = node.child
        node.child = ir.ClockedEdge(ui())
        node = node.child
        node.child = ir.DoneNode(ui())

        OptimizeGraph(head.child)
        cases = CaseBuilder(head.child, ir.Context()).get_case()
        logging.error(cases.to_string())
