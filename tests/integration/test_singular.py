import inspect
import logging
import warnings
from pathlib import Path
from types import FunctionType
from typing import Union
from unittest import TestCase

import pytest
from parameterized import parameterized

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


@pytest.mark.usefixtures("argparse")
class TestComplete(TestCase):
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
    def test_single_performance(
        self, func: FunctionType, test_cases: list[Union[tuple[int, ...], int]]
    ):
        for opti_level in self.args.optimization_levels:
            ns = {}
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
    def test_single_correctness(
        self, func: FunctionType, test_cases: list[Union[tuple[int, ...], int]]
    ):
        for opti_level in self.args.optimization_levels:
            ns = {}
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
                module, testbench, namespace_to_file(file_stem, ns, config)
                context = get_context(verilogified)
                cmd = iverilog.make_cmd(
                    context.testbench_name,
                    [file_stem + ".sv", file_stem + "_tb.sv"],
                )
                logging.info(cmd)

            expected = list(get_expected(verilogified))
            assert "urandom_range" in testbench
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
