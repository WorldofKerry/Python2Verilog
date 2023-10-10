import unittest

from python2verilog import ir
from python2verilog.api import get_context, verilogify
from python2verilog.api.namespace import namespace_to_verilog
from python2verilog.backend import verilog
from python2verilog.backend.verilog.codegen import CaseBuilder
from python2verilog.frontend.generator import GeneratorFunc


class TestFresh(unittest.TestCase):
    def test_main(self):
        ns = {}

        @verilogify(namespace=ns)
        def my_func():
            # b = 0
            # while b < 20:
            #     if b == 15:
            #         yield b
            #     b = b + 1
            # yield b + 420
            n = 10
            a, b = 0, 1
            count = 1
            while count < n:
                yield a
                a, b = b, a + b
                count += 1

        my_func()

        root, cxt = GeneratorFunc(get_context(my_func)).create_root()
        case = CaseBuilder(root, ir.Context.empty_valid()).get_case()
        sv = verilog.CodeGen(root, cxt).get_module_str()
        with open("./new.sv", mode="w") as f:
            f.write(str(sv))

        root, cxt = GeneratorFunc(get_context(my_func)).create_root()
        case = CaseBuilder(root, cxt).get_case()
        sv = verilog.CodeGen(root, cxt).get_module_str()
        with open("./old.sv", mode="w") as f:
            f.write(str(sv))

        # module, testbench = namespace_to_verilog(ns)

        return
