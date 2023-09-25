"""
Test suite for functions that call other functions
"""

import inspect
import logging
import warnings
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
from python2verilog.backend.verilog.config import CodegenConfig
from python2verilog.simulation import iverilog

from .functions import *
from .utils import make_tuple, name_func

PARAMETERS = (
    [
        ([olympic_logo, colored_circle], [(10, 10, 4), (13, 13, 7)]),
    ],
)


@pytest.mark.usefixtures("argparse")
class TestComplete(TestCase):
    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_multi_performance(
        self, funcs: list[FunctionType], test_cases: list[Union[tuple[int, ...], int]]
    ):
        for opti_level in self.args.optimization_levels:
            ns = {}

            for func in reversed(funcs):  # First function is tested upon
                verilogified = verilogify(
                    namespace=ns, optimization_level=opti_level, mode=Modes.OVERWRITE
                )(func)

            for case in test_cases:
                case = make_tuple(case)
                verilogified(*case)

            config = CodegenConfig(random_ready=False)
            module, testbench = namespace_to_verilog(ns, config)
            if self.args.write:
                file_stem = str(
                    Path(__file__).parent
                    / (self.__dict__["_testMethodName"] + f"::O{opti_level}").replace(
                        "::", "_"
                    )
                )
                namespace_to_file(file_stem, ns, config)
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

    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_multi_correctness(
        self, funcs: list[FunctionType], test_cases: list[Union[tuple[int, ...], int]]
    ):
        for opti_level in self.args.optimization_levels:
            ns = {}

            for func in reversed(funcs):  # First function is tested upon
                verilogified = verilogify(
                    namespace=ns, optimization_level=opti_level, mode=Modes.OVERWRITE
                )(func)

            for case in test_cases:
                case = make_tuple(case)
                verilogified(*case)

            config = CodegenConfig(random_ready=True)
            module, testbench = namespace_to_verilog(ns, config)
            if self.args.write:
                file_stem = str(
                    Path(__file__).parent
                    / (self.__dict__["_testMethodName"] + f"::O{opti_level}").replace(
                        "::", "_"
                    )
                )
                config = CodegenConfig(random_ready=False)
                namespace_to_file(file_stem, ns, config)
                context = get_context(verilogified)
                cmd = iverilog.make_cmd(
                    context.testbench_name,
                    [file_stem + ".sv", file_stem + "_tb.sv"],
                )
                logging.info(cmd)

            assert "urandom_range" in testbench
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
