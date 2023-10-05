"""
Test suite for functions that call other functions
"""

from types import FunctionType
from typing import Iterable, Union
from unittest import TestCase

import pytest
from parameterized import parameterized

from .base_tests import BaseTest
from .functions import *
from .utils import name_func

PARAMETERS = [
    ([double_for, hrange], [3, 20]),
    ([dupe, hrange], [(0, 1, 10), (3, 7, 73)]),
    ([olympic_logo_naive, circle_lines], [(10, 10, 4), (13, 13, 7)]),
    (
        [olympic_logo, olympic_logo_mids, circle_lines],
        [(10, 10, 4), (13, 13, 7)],
    ),
]


@pytest.mark.usefixtures("argparse")
class TestMulti(TestCase, BaseTest):
    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_perf(
        self,
        funcs: Iterable[FunctionType],
        test_cases: Iterable[Union[tuple[int, ...], int]],
    ):
        BaseTest.test_perf(self, funcs, test_cases)

    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_correct(
        self,
        funcs: Iterable[FunctionType],
        test_cases: Iterable[Union[tuple[int, ...], int]],
    ):
        BaseTest.test_correct(self, funcs, test_cases)

    @classmethod
    def tearDownClass(cls):
        BaseTest.make_statistics(cls)
