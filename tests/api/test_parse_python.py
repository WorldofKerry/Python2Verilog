import logging
import unittest
import ast

from python2verilog.api import parse_python


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
        logging.warning(repr(parse_python(code, "nuts")))

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
