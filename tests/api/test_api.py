import atexit
from functools import wraps
import os
from pathlib import Path
import unittest

from python2verilog.api.wrappers import text_to_context
from python2verilog.api.decorator import new_namespace, verilogify, global_namespace


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
        text_to_context(code, "nuts")
        # logging.debug(func_ast)

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
        self.assertRaises(AssertionError, text_to_context, code, "nuts")

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
        self.assertRaises(AssertionError, text_to_context, code, "nuts")


class TestVerilogify(unittest.TestCase):
    def writes(func):
        """
        Decorator to clean up written .sv files
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)

            dir = Path(__file__).parent.absolute()
            filenames = os.listdir(dir)
            for filename in filenames:
                if filename.endswith(".sv"):
                    os.remove(os.path.join(dir, filename))

        return wrapper

    @classmethod
    @writes
    def setUp(cls):
        pass

    @writes
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

        for key, value in global_namespace.items():
            print(type(key), type(value))

    @writes
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
