import ast as pyast
import inspect
import textwrap
import unittest

from python2verilog import ir
from python2verilog.backend.verilog.codegen import CaseBuilder
from python2verilog.frontend.fresh import GeneratorFunc


class TestFresh(unittest.TestCase):
    def test_main(self):
        def my_func():
            a = 0
            b = 1
            while 1:
                b = b + 1
                break
            yield a

        inst = my_func()
        # for e in inst:
        #     print(e)

        full_tree = pyast.parse(textwrap.dedent(inspect.getsource(my_func)))
        func_tree = full_tree.body[0]

        result = GeneratorFunc(func_tree).parse_func()
        # dummy = ir.BasicNode(
        #     unique_id="DUMMMMY",
        #     child=ir.NonClockedEdge(unique_id="DUMMY", child=result),
        # )
        case = CaseBuilder(result, ir.Context().from_validated()).get_case()
        print(str(case))

        return
