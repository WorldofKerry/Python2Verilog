import ast as pyast
import inspect
import textwrap
import unittest

from python2verilog import ir
from python2verilog.api import verilogify, get_context
from python2verilog.backend.verilog.codegen import CaseBuilder
from python2verilog.frontend.fresh import GeneratorFunc
from python2verilog.frontend.generator import FromGenerator


class TestFresh(unittest.TestCase):
    def test_main(self):

        def my_func():
            # b = 0
            # while b < 20:
            #     if b % 2 == 0:
            #         yield b
            #         continue
            #     if b == 7:
            #         break
            #     b = b + 1

            # location
            # prev_tails
            
            # a = b + 2 # here
            if 1:
                a = 1
                if 1:
                    a = 1
                    if 1:
                        a = 1
                        if 1:
                            a = 1
            yield 10

        inst = my_func()
        # for e in inst:
        #     print(e)

        full_tree = pyast.parse(textwrap.dedent(inspect.getsource(my_func)))
        func_tree = full_tree.body[0]
        print(pyast.dump(func_tree, indent=2))

        result = GeneratorFunc(func_tree).parse_func()
        case = CaseBuilder(result, ir.Context().from_validated()).get_case()
        # dummy = ir.BasicNode(
        #     unique_id="DUMMMMY",
        #     child=ir.NonClockedEdge(unique_id="DUMMY", child=result),
        # )
        case = CaseBuilder(result, ir.Context.from_validated()).get_case()
        print(str(case))
        
        ns = {}
        wrapped = verilogify(namespace=ns)(my_func)
        wrapped()
        old_result = FromGenerator(get_context(wrapped)).create_root()

        return