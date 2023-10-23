import ast
import unittest

import llvmlite.binding as llvm
from llvmlite import ir

from python2verilog.optimizer.llvm import *


class TestLLVM(unittest.TestCase):
    def test_all(self):
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        string = """
second = 7 * (a + b)
first = ((a + b) * (a + b)) - (5 / ((a + b) * (a + b)))
        """
        #     string = """
        # result = ((a + b) * (a + b)) - (5 / ((a + b) * (a + b)))
        # """
        tree = ast.parse(string)
        print(ast.dump(tree, indent="\t"))

        # Create some useful types
        # basic_type = ir.IntType(32)
        basic_type = ir.PointerType(ir.IntType(32))
        fnty = ir.FunctionType(
            ir.VoidType(), (basic_type, basic_type, basic_type, basic_type)
        )

        # Create an empty module...
        module = ir.Module(name="bruv")

        # and declare a function named "fpadd" inside it
        func = ir.Function(module, fnty, name="add")

        # Now implement the function
        block = func.append_basic_block(name="entry")

        llvm_builder = ir.IRBuilder(block)
        inputs = {"a": func.args[0], "b": func.args[1]}
        ast_to_builder(tree, llvm_builder, inputs, func.args)
        llvm_builder.ret_void()

        llmod = llvm.parse_assembly(str(func))
        print(llmod)

        optimize(llmod)
        print(llmod)

        add = llmod.get_function("add")

        # print(dir(add))
        code = ""
        print("STARTING CODEGEN")
        mapping = dict(inputs)
        print("mapping", mapping)
        for block in add.blocks:
            for instr in block.instructions:
                if str(instr.opcode) == "store":
                    replace_loads(instr, inputs)
                    print("store", instr)
                    continue
                if str(instr.opcode) == "load":
                    continue
                code += str(instr) + "\n"
        print("CODE")
        print(code)
