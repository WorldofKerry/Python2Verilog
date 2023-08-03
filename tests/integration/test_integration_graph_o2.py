import unittest
import ast
import warnings
import os
import configparser
import subprocess
import csv
import copy
import re
import logging
import pathlib
import pandas as pd
import pytest
import networkx as nx
from matplotlib import pyplot as plt

from python2verilog.backend.verilog import CodeGen, CaseBuilder
from python2verilog.frontend import Generator2Graph
from python2verilog.optimizer import basic, OptimizeGraph
from python2verilog.convert import *
from python2verilog.ir import *
from python2verilog.utils.visualization import make_visual
from .integration_graph_templates import generic_run_test


@pytest.mark.usefixtures("argparse")  # creates self.args
class TestMain(unittest.TestCase):
    all_statistics: list[dict] = []

    def tearDownClass():
        df = pd.DataFrame(
            TestMain.all_statistics, columns=TestMain.all_statistics[0].keys()
        )
        print("\n" + df.to_markdown(index=False))

    @staticmethod
    def create_verilog_from_func(function: ast.FunctionDef):
        ir, context = Generator2Graph(function).results
        OptimizeGraph(ir, threshold=2)
        verilog = CodeGen.from_optimal_ir(ir, context)
        return verilog, ir

    def test_circle_lines(self):
        test_cases = [(21, 37, 7), (89, 45, 43)]
        generic_run_test(
            self,
            "circle_lines",
            test_cases,
            self.args,
            f"data/{pathlib.Path(__file__).stem.replace('test_', '')}/",
            self.create_verilog_from_func,
        )

    def test_happy_face(self):
        test_cases = [(50, 51, 7), (86, 97, 43)]
        generic_run_test(
            self,
            "happy_face",
            test_cases,
            self.args,
            f"data/{pathlib.Path(__file__).stem.replace('test_', '')}/",
            self.create_verilog_from_func,
        )

    def test_rectangle_filled(self):
        test_cases = [(32, 84, 5, 7), (64, 78, 34, 48)]
        generic_run_test(
            self,
            "rectangle_filled",
            test_cases,
            self.args,
            f"data/{pathlib.Path(__file__).stem.replace('test_', '')}/",
            self.create_verilog_from_func,
        )

    def test_rectangle_lines(self):
        test_cases = [(32, 84, 5, 7), (84, 96, 46, 89)]
        generic_run_test(
            self,
            "rectangle_lines",
            test_cases,
            self.args,
            f"data/{pathlib.Path(__file__).stem.replace('test_', '')}/",
            self.create_verilog_from_func,
        )

    def test_fib(self):
        test_cases = [(10,), (35,)]
        generic_run_test(
            self,
            "fib",
            test_cases,
            self.args,
            f"data/{pathlib.Path(__file__).stem.replace('test_', '')}/",
            self.create_verilog_from_func,
        )

    def test_testing(self):
        test_cases = [(15,)]
        generic_run_test(
            self,
            "testing",
            test_cases,
            self.args,
            f"data/{pathlib.Path(__file__).stem.replace('test_', '')}/",
            self.create_verilog_from_func,
        )
