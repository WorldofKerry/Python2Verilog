import atexit
import logging
import os
from pathlib import Path
import unittest
import ast
import warnings

from python2verilog.api import parse_python, global_scope
from python2verilog.api.api import new_namespace, verilogify


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
    def test_basic(self):
        @verilogify(write=True)
        def counter0(n):
            i = 0
            while i < n:
                yield (i)
                i += 1

        @verilogify
        def counter1(n, other):
            i = 0
            while i < n:
                yield (i)
                i += 1

        for value in counter0(5):
            print(value)

        counter0(10)
        counter1(15, 20)

        for key, value in global_scope.items():
            print(type(key), type(value))
        TestVerilogify.cleanup_files()

    def test_overwrite_fail(self):
        @verilogify(write=True)
        def counter_overwrite(n):
            i = 0
            while i < n:
                yield (i)
                i += 1

        counter_overwrite(10)

        def inner():
            try:

                @verilogify(write=True, namespace=new_namespace())
                def counter_overwrite(n):
                    i = 0
                    while i < n:
                        yield (i)
                        i += 1

                counter_overwrite(10)
            except FileExistsError as e:
                raise e

        self.assertRaises(FileExistsError, inner)

        TestVerilogify.cleanup_files()

    @staticmethod
    def cleanup_files():
        dir = Path(__file__).parent.absolute()
        filenames = os.listdir(dir)
        for filename in filenames:
            if filename.endswith(".sv"):
                os.remove(os.path.join(dir, filename))
