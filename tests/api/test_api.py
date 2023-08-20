import atexit
import logging
import unittest
import ast

from python2verilog.api import parse_python, global_scope
from python2verilog.api.api import verilogify


class TestParsePython(unittest.TestCase):
    def test_parse_python(self):
        code = """
def nuts(input, other):
  yield input, input
  yield input + 1, input

def deeznuts(input):
  yield input
  yield input + 1

inst = nuts(50, 51)
inst = nuts(15, 16)
inst = deeznuts(420)
"""
        context, func_ast, func_callable = parse_python(code, "nuts")
        logging.debug(func_ast)

    # def test_this_file(self):
    #     with open(__file__, mode="r") as f:
    #         # logging.warning(parse_python(f.read(), "test_parse_python"))
    #         self.assertRaises(RuntimeError, parse_python, f.read(), "test_parse_python")

    def test_mix_types(self):
        code = """
def nuts(input, other):
  yield input, input
  yield input + 1, input

def deeznuts(input):
  yield input
  yield input + 1

inst = nuts(50, 51)
inst = nuts(15, "16")
inst = deeznuts(420)
"""
        self.assertRaises(AssertionError, parse_python, code, "nuts")

        code = """
def nuts(input, other):
  yield input, input
  yield input + 1, "bruv"

def deeznuts(input):
  yield input
  yield input + 1

inst = nuts(50, 51)
inst = nuts(15, 16)
inst = deeznuts(420)
"""
        self.assertRaises(AssertionError, parse_python, code, "nuts")


class TestVerilogify(unittest.TestCase):
    def test_main(self):
        @verilogify
        def my_counter(n):
            i = 0
            while i < n:
                yield (i)
                i += 1

        @verilogify(module_path="ayy lmao")
        def my_counter2(n, other):
            i = 0
            while i < n:
                yield (i)
                i += 1

        for value in my_counter(5):
            print(value)
        my_counter(10)
        my_counter2(15, 20)

        for key, value in global_scope.items():
            print(type(key), type(value))

        def exit_handler():
            for key, value in global_scope.items():
                print(
                    value.name, value.test_cases, value.input_types, value.output_types
                )

        atexit.register(exit_handler)
