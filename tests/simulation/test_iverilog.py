import unittest
from python2verilog.extern.iverilog import make_iverilog_cmd


class TestIVerilog(unittest.TestCase):
    def test_basics(self):
        result = make_iverilog_cmd("name", ["a.sv", "b.sv"])
        self.assertTrue(result)
