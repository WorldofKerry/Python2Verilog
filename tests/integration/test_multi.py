"""
Test suite for functions that call other functions
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
    # ([double_for, hrange], [3, 20]),
    ([olympic_logo, colored_circle], [(10, 10, 4), (13, 13, 7)]),
    ([dupe, hrange], [(0, 1, 10), (3, 7, 25)]),
]


@pytest.mark.usefixtures("argparse")
class TestMulti(TestCase, BaseTest):
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
