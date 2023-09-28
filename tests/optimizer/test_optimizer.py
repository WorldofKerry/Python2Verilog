import logging
import unittest
import warnings

from python2verilog import ir
from python2verilog.backend.verilog import CodeGen
from python2verilog.optimizer import graph_apply_mapping
from python2verilog.optimizer.optimizer import graph_update_mapping


class TestGraphApplyMapping(unittest.TestCase):
    def test_update_mapping(self):
        a = ir.Var("a")
        b = ir.Var("b")
        c = ir.Var("c")
        zero = ir.Int(0)
        one = ir.Int(1)

        changes = [a, zero], [b, one], [c, zero], [a, b], [b, c], [c, ir.Add(a, b)]

        mapping = {}
        for key, value in changes:
            logging.error(f"{key} = {value}")
            node = ir.AssignNode(unique_id="", lvalue=key, rvalue=value)
            lvalue, rvalue = graph_apply_mapping(node, mapping)
            node = ir.AssignNode(unique_id="", lvalue=lvalue, rvalue=rvalue)
            mapping = graph_update_mapping(node, mapping)
            logging.error(mapping)

    def test_independent(self):
        """
        i <= constant
        """
        mapping = {ir.Var("i"): ir.Add(ir.Var("i"), ir.Int(1))}
        node = ir.AssignNode(
            unique_id="abc",
            lvalue=ir.Var("i"),
            rvalue=ir.Add(ir.Int(0), ir.Int(1)),
        )
        updated = graph_apply_mapping(node, mapping)
        self.assertEqual("_i <= $signed($signed(0) + $signed(1))", updated.verilog())

        mapping = {ir.Var("i"): ir.Add(ir.Var("i"), ir.Var("i"))}
        node = ir.AssignNode(
            unique_id="abc",
            lvalue=ir.Var("i"),
            rvalue=ir.Add(ir.Int(0), ir.Int(1)),
        )
        updated = graph_apply_mapping(node, mapping)
        self.assertEqual("_i <= $signed($signed(0) + $signed(1))", updated.verilog())

        mapping = {ir.Var("i"): ir.Add(ir.Int(0), ir.Int(1))}
        node = ir.AssignNode(
            unique_id="abc",
            lvalue=ir.Var("i"),
            rvalue=ir.Add(ir.Int(0), ir.Int(1)),
        )
        updated = graph_apply_mapping(node, mapping)
        self.assertEqual("_i <= $signed($signed(0) + $signed(1))", updated.verilog())


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
