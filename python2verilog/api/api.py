"""
Wrappers
"""

import argparse
import os
import ast
import warnings
from typing import Optional
from ..frontend import Generator2Graph
from ..backend.verilog import CodeGen
from ..optimizer import OptimizeGraph


def convert_graph(func: ast.FunctionDef, optimization_level: int):
    """
    Wrapper for Python to Verilog conversion
    """
    return convert_graph_debug(func, optimization_level)[0]


def convert_graph_debug(func: ast.FunctionDef, optimization_level: int):
    """
    Wrapper for Python to Verilog conversion
    """
    ir, context = Generator2Graph(func).results
    if optimization_level > 0:
        OptimizeGraph(ir, threshold=optimization_level - 1)
    return CodeGen(ir, context), ir
