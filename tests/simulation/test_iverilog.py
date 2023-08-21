import unittest
from python2verilog.simulation.iverilog import run_iverilog


class TestIVerilog(unittest.TestCase):
    def test_basics(self):
        result = run_iverilog("name", ["a.sv", "b.sv"])
