"""
Test suite for basic functions
"""

from types import FunctionType
from typing import Union
from unittest import TestCase

import pytest
from parameterized import parameterized

from .bases import BaseTest
from .functions import *
from .utils import name_func

PARAMETERS = [
    (fib, [(10)]),
    (floor_div, [(13)]),
    (operators, [(13, 17)]),
    (multiplier, [(13, 17)]),
    (division, [(6, 7, 10), (2, 3, 10)]),
    (circle_lines, [(10, 10, 4), (13, 13, 7)]),
    (happy_face, [(10, 10, 4), (13, 13, 7)]),
    (rectangle_filled, [(10, 10, 4, 5), (13, 13, 7, 11)]),
    (rectangle_lines, [(10, 10, 4, 5), (13, 13, 7, 11)]),
]


@pytest.mark.usefixtures("argparse")
class TestSingle(TestCase, BaseTest):
    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_multi_perf(
        self, funcs: list[FunctionType], test_cases: list[Union[tuple[int, ...], int]]
    ):
        BaseTest.multi_perf(self, funcs, test_cases)

    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_multi_correct(
        self, funcs: list[FunctionType], test_cases: list[Union[tuple[int, ...], int]]
    ):
        BaseTest.multi_correct(self, funcs, test_cases)

    @classmethod
    def tearDownClass(cls):
        BaseTest.make_statistics(cls)
