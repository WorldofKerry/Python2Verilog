"""
Test suite for functions that call other functions
"""

import inspect
import logging
import os
import re
import subprocess
import warnings
from pathlib import Path
from types import FunctionType
from typing import Union
from unittest import TestCase

import pandas as pd
import pytest
from parameterized import parameterized

from python2verilog import (
    Modes,
    get_actual_raw,
    get_context,
    get_expected,
    namespace_to_file,
    namespace_to_verilog,
    verilogify,
)
from python2verilog.api.verilogify import get_actual
from python2verilog.backend.verilog.config import CodegenConfig
from python2verilog.simulation import iverilog
from python2verilog.simulation.display import strip_ready, strip_valid

from .bases import BaseTest
from .functions import *
from .utils import make_tuple, name_func

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
