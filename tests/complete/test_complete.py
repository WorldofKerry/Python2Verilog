import inspect
import logging
from pathlib import Path
from types import FunctionType
from typing import Union
from unittest import TestCase

import pytest
from parameterized import parameterized, parameterized_class

from python2verilog import (
    Modes,
    get_actual,
    get_context,
    get_expected,
    namespace_to_file,
    namespace_to_verilog,
    verilogify,
)
from python2verilog.simulation import iverilog

from .functions import *


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

    def name_func(testcase_func: FunctionType, param_num: int, param: dict) -> str:
        """
        Custom name function

        Stores in _testMethodName
        """
        return f"{testcase_func.__name__}::{param.args[0].__name__}::{param_num}"

    @parameterized.expand(
        [
            (fib, [(10)]),
            (floor_div, [(13)]),
            (operators, [(13, 17)]),
            (multiplier, [(13, 17)]),
            (division, [(6, 7, 10), (2, 3, 10)]),
            (circle_lines, [(10, 10, 4), (13, 13, 7)]),
            (happy_face, [(10, 10, 4), (13, 13, 7)]),
            (rectangle_filled, [(10, 10, 4, 5), (13, 13, 7, 11)]),
            (rectangle_lines, [(10, 10, 4, 5), (13, 13, 7, 11)]),
        ],
        name_func=name_func,
    )
    def test_performance(
        self, func: FunctionType, test_cases: list[Union[tuple[int, ...], int]]
    ):
        for opti_level in self.args.optimization_levels:
            ns = {}
            verilogified = verilogify(
                namespace=ns, optimization_level=opti_level, mode=Modes.OVERWRITE
            )(func)

            for case in test_cases:
                case = self.make_tuple(case)
                verilogified(*case)

                test_name = str(
                    Path(__file__).parent
                    / (self.__dict__["_testMethodName"] + f"::O{opti_level}").replace(
                        "::", "_"
                    )
                )

            module, testbench = namespace_to_verilog(ns)
            other_mod, other_tb = namespace_to_file(test_name, ns)
            bruv = reversed(["lmao"])

            if self.args.write:
                # mod_path = Path(__file__).parent / (test_name + ".sv")
                # tb_path = Path(__file__).parent / (test_name + "_tb.sv")
                with open(Path(__file__).parent / ("other.sv"), mode="w") as f:
                    f.write(str(module))
                # with open(tb_path, mode="w") as f:
                #     f.write(str(testbench))

                context = get_context(verilogified)
                cmd = iverilog.make_cmd(
                    context.testbench_name,
                    [test_name + ".sv", test_name + "_tb.sv"],
                )
                logging.error(cmd)

            expected = list(get_expected(verilogified))
            actual = list(
                get_actual(
                    verilogified, module, testbench, timeout=1 + len(expected) // 64
                )
            )
            logging.warning(actual)
            self.assertTrue(len(actual) > 0)
            self.assertListEqual(actual, expected)
