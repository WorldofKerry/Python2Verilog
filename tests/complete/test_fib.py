import logging
from unittest import TestCase

import pytest
from parameterized import parameterized, parameterized_class

from python2verilog import get_actual, get_expected, namespace_to_verilog, verilogify

from .functions import circle_lines, fib


@pytest.mark.usefixtures("argparse")
class TestComplete(TestCase):
    @staticmethod
    def make_tuple(input: int | tuple[int]) -> tuple[int]:
        """
        Makes input into a tuple if it is not a tuple
        """
        if not isinstance(input, tuple):
            return (input,)
        return input

    def name_func(testcase_func, param_num, param):
        """
        Custom test case name
        """
        return f"{testcase_func.__name__}::{param.args[0].__name__}"

    @parameterized.expand(
        [(fib, [(10)]), (circle_lines, [(10, 10, 4)])], name_func=name_func
    )
    def test_performance(self, func, test_cases):
        ns = {}
        verilogified = verilogify(namespace=ns)(func)

        for case in test_cases:
            case = self.make_tuple(case)
            verilogified(*case)

        module, testbench = namespace_to_verilog(ns)
        # mod_path = Path(__file__).parent / "o0.sv"
        # tb_path = Path(__file__).parent / "o0_tb.sv"
        # with open(mod_path, mode="w") as f:
        #     f.write(str(module))
        # with open(tb_path, mode="w") as f:
        #     f.write(str(testbench))
        # cmd = iverilog.make_cmd(
        #     "dup_range_goal_tb",
        #     [mod_path, tb_path],
        # )
        # warnings.warn(cmd)

        expected = list(get_expected(verilogified))
        actual = list(
            get_actual(verilogified, module, testbench, timeout=1 + len(expected) // 64)
        )
        self.assertTrue(len(actual) > 2)
        self.assertListEqual(actual, expected)
