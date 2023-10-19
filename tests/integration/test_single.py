"""
Test suite for basic functions
"""

from types import FunctionType
from typing import Union

import pytest
from parameterized import parameterized

from .base_tests import BaseTestWrapper
from .functions import *
from .utils import name_func

PARAMETERS = [
    (keyword_test, [()]),
    (fib, range(10, 31, 10)),
    (floor_div, [13, 23]),
    (operators, [(31, 13), (-31, 13), (31, -13), (-31, -13)]),
    (multiplier, [(13, 17), (78, 67)]),
    (multiplier_func, [(13, 17), (78, 67)]),
    (hrange, [(0, 1, 10), (0, 1, 1000)]),
    (division, [(6, 7, 10), (2, 3, 30), (13, 17, 5)]),
    (circle_lines, [(21, 37, 7), (79, 45, 43)]),
    (happy_face, [(50, 51, 7), (76, 97, 43)]),
    (rectangle_filled, [(32, 84, 5, 7), (64, 78, 23, 27)]),
    (rectangle_lines, [(32, 84, 5, 7), (84, 96, 46, 89)]),
]


@pytest.mark.usefixtures("argparse")
class TestSingle(BaseTestWrapper.BaseTest):
    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_perf(
        self, funcs: list[FunctionType], test_cases: list[Union[tuple[int, ...], int]]
    ):
        BaseTestWrapper.BaseTest.test_perf(self, funcs, test_cases)

    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_correct(
        self, funcs: list[FunctionType], test_cases: list[Union[tuple[int, ...], int]]
    ):
        BaseTestWrapper.BaseTest.test_correct(self, funcs, test_cases)

    @classmethod
    def tearDownClass(cls):
        BaseTestWrapper.BaseTest.make_statistics(cls)
