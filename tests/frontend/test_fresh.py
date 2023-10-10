import ast as pyast
import inspect
import textwrap
import unittest

from python2verilog import ir
from python2verilog.api import get_context, verilogify
from python2verilog.api.namespace import namespace_to_verilog
from python2verilog.backend.verilog.codegen import CaseBuilder
from python2verilog.frontend.fresh import GeneratorFunc
from python2verilog.frontend.generator import FromGenerator


class TestFresh(unittest.TestCase):
    def test_main(self):
        ns = {}

        @verilogify(namespace=ns)
        def my_func():
            b = 0
            while b < 20:
                if b == 15:
                    yield b
                b = b + 1
            yield b + 420

        inst = my_func()
        # for e in inst:
        #     print(e)

        full_tree = pyast.parse(textwrap.dedent(inspect.getsource(my_func)))
        func_tree = full_tree.body[0]
        print(pyast.dump(func_tree, indent=2))

        result = GeneratorFunc(func_tree).parse_func()
        case = CaseBuilder(result, ir.Context.from_validated()).get_case()
        # dummy = ir.BasicNode(
        #     unique_id="DUMMMMY",
        #     child=ir.NonClockedEdge(unique_id="DUMMY", child=result),
        # )
        case = CaseBuilder(result, ir.Context.from_validated()).get_case()
        print(str(case))

        root, cxt = FromGenerator(get_context(my_func)).create_root()
        case = CaseBuilder(root, cxt).get_case()
        print(str(case))

        # module, testbench = namespace_to_verilog(ns)

        return
