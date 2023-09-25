"""
Tests for multi-function structures

e.g. functions with function calls
"""

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
    def make_tuple(input: Union[int, tuple[int]]) -> tuple[int]:
        """
        Makes input into a tuple if it is not a tuple
        """
        if not isinstance(input, tuple):
            return (input,)
        return input

    @staticmethod
    def name_func(testcase_func: FunctionType, param_num: int, param: dict) -> str:
        """
        Custom name function

        Stores in _testMethodName
        """
        if isinstance(param.args[0], FunctionType):
            return f"{testcase_func.__name__}::{param.args[0].__name__}::{param_num}"
        else:
            # If list of functions take first
            return f"{testcase_func.__name__}::{param.args[0][0].__name__}::{param_num}"

    @parameterized.expand(
        [
            ([olympic_logo, colored_circle], [(10, 10, 4), (13, 13, 7)]),
        ],
        name_func=name_func,
    )
    def test_performance_multi(
        self, funcs: list[FunctionType], test_cases: list[Union[tuple[int, ...], int]]
    ):
        for opti_level in self.args.optimization_levels:
            ns = {}

            for func in reversed(funcs):  # First function is tested upon
                verilogified = verilogify(
                    namespace=ns, optimization_level=opti_level, mode=Modes.OVERWRITE
                )(func)

            for case in test_cases:
                case = self.make_tuple(case)
                verilogified(*case)

            module, testbench = namespace_to_verilog(ns)
            if self.args.write:
                file_stem = str(
                    Path(__file__).parent
                    / (self.__dict__["_testMethodName"] + f"::O{opti_level}").replace(
                        "::", "_"
                    )
                )
                namespace_to_file(file_stem, ns)
                context = get_context(verilogified)
                cmd = iverilog.make_cmd(
                    context.testbench_name,
                    [file_stem + ".sv", file_stem + "_tb.sv"],
                )
                logging.info(cmd)

            expected = list(get_expected(verilogified))
            actual = list(
                get_actual(
                    verilogified, module, testbench, timeout=1 + len(expected) // 64
                )
            )
            logging.info(
                f"Actual len {len(actual)}: {str(actual[:min(len(actual), 5)])[:-1]}, ...]"
            )
            self.assertTrue(len(actual) > 0)
            self.assertListEqual(actual, expected)
