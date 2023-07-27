import unittest
import ast
import warnings

from python2verilog.optimizer import *
from python2verilog import ir
from python2verilog.backend import Verilog


class TestGraphApplyMapping(unittest.TestCase):
    def test_dependent(self):
        """
        i <= f(i)
        """
        mapping = {ir.Var("i"): ir.Int(1)}
        node = ir.AssignNode(
            unique_id="abc", lvalue=ir.Var("i"), rvalue=ir.Add(ir.Var("i"), ir.Int(1))
        )
        self.assertTrue(is_dependent(node.rvalue, str(node.lvalue)))
        updated = graph_apply_mapping(node, mapping)
        self.assertEqual("i <= (1 + 1)", str(updated))

        mapping = {ir.Var("i"): ir.Add(ir.Var("i"), ir.Int(1))}
        node = ir.AssignNode(
            unique_id="abc", lvalue=ir.Var("i"), rvalue=ir.Add(ir.Var("i"), ir.Int(1))
        )
        self.assertTrue(is_dependent(node.rvalue, str(node.lvalue)))
        updated = graph_apply_mapping(node, mapping)
        self.assertEqual("i <= ((i + 1) + 1)", str(updated))

    def test_independent(self):
        """
        i <= constant
        """
        mapping = {ir.Var("i"): ir.Add(ir.Var("i"), ir.Int(1))}
        node = ir.AssignNode(
            unique_id="abc", lvalue=ir.Var("i"), rvalue=ir.Add(ir.Int(0), ir.Int(1))
        )
        self.assertFalse(is_dependent(node.rvalue, str(node.lvalue)))
        updated = graph_apply_mapping(node, mapping)
        self.assertEqual("i <= ((0 + 1) + 1)", str(updated))

        mapping = {ir.Var("i"): ir.Add(ir.Var("i"), ir.Var("i"))}
        node = ir.AssignNode(
            unique_id="abc", lvalue=ir.Var("i"), rvalue=ir.Add(ir.Int(0), ir.Int(1))
        )
        self.assertFalse(is_dependent(node.rvalue, str(node.lvalue)))
        updated = graph_apply_mapping(node, mapping)
        self.assertEqual("i <= ((0 + 1) + (0 + 1))", str(updated))

        mapping = {ir.Var("i"): ir.Add(ir.Int(0), ir.Int(1))}
        node = ir.AssignNode(
            unique_id="abc", lvalue=ir.Var("i"), rvalue=ir.Add(ir.Int(0), ir.Int(1))
        )
        self.assertFalse(is_dependent(node.rvalue, str(node.lvalue)))
        updated = graph_apply_mapping(node, mapping)
        # self.assertEqual("i <= ((0 + 1) + (0 + 1))", str(updated))


# class TestOptimizer(unittest.TestCase):
#     def test_replace_single_case(self):
#         python = """
# def foo(x) -> tuple[int]:
#     if x > 0:
#         yield 1
#     else:
#         yield 1
# """
#         tree = ast.parse(python)
#         function = tree.body[0]
#         ir, context = GeneratorParser(function).get_results()
#         ir = replace_single_case(ir)
#         verilog = Verilog().from_ir(ir, context)
#         # warnings.warn(verilog.get_module().to_string())

#     def test_optimize_if(self):
#         python = """
# def foo(x) -> tuple[int]:
#     if x > 0:
#         yield 1
#     else:
#         yield 1
# """
#         tree = ast.parse(python)
#         function = tree.body[0]
#         ir, context = GeneratorParser(function).get_results()
#         ir = replace_single_case(ir)
#         ir = optimize_if(ir)
#         verilog = Verilog().from_ir(ir, context)
#         # warnings.warn(verilog.get_module().to_string())

#     def test_combine_cases(self):
#         """
#         NEXT
#         NEXT
#         NEXT
#         """
#         # Optimizable
#         python = """
# def foo(x, y, z) -> tuple[int]:
#     a = x + y
#     b = x + 1
#     c = x + z + 2
# """
#         tree = ast.parse(python)
#         function = tree.body[0]
#         ir, context = GeneratorParser(function).get_results()
#         ir = combine_cases(ir)
#         self.assertEqual(len(ir.case_items), 1)
#         verilog = Verilog().from_ir(ir, context)
#         # warnings.warn(verilog.get_module().to_string())

#         # Not Optimizable - dependent variables
#         python = """
# def foo(x) -> tuple[int]:
#     c = x
#     a = x
#     b = a
# """
#         tree = ast.parse(python)
#         function = tree.body[0]
#         ir, context = GeneratorParser(function).get_results()
#         ir = combine_cases(ir)
#         self.assertEqual(len(ir.case_items), 2)
#         verilog = Verilog().from_ir(ir, context)
#         # warnings.warn(verilog.get_module().to_string())

#         # Not Optimizable - dependent yield
#         python = """
# def foo(x) -> tuple[int]:
#     a = x
#     yield (a,)
# """
#         tree = ast.parse(python)
#         function = tree.body[0]
#         ir, context = GeneratorParser(function).get_results()
#         ir = combine_cases(ir)
#         self.assertEqual(len(ir.case_items), 2)
#         verilog = Verilog().from_ir(ir, context)
#         # warnings.warn(verilog.get_module().to_string())

#         # Not Optimizable - multiple yields
#         python = """
# def foo(x) -> tuple[int]:
#     yield (x,)
#     yield (x,)
# """
#         tree = ast.parse(python)
#         function = tree.body[0]
#         ir, context = GeneratorParser(function).get_results()
#         ir = combine_cases(ir)
#         self.assertEqual(len(ir.case_items), 2)
#         verilog = Verilog().from_ir(ir, context)
#         # warnings.warn(verilog.get_module().to_string())
