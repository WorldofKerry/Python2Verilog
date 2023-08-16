"""
Wrappers
"""

import argparse
import logging
import os
import ast
import warnings
from typing import Optional

from python2verilog.utils.assertions import assert_type
from ..frontend import Generator2Graph
from .. import ir
from ..backend import verilog
from ..optimizer import OptimizeGraph


def convert_generator(func: ast.FunctionDef, optimization_level: int):
    """
    Wrapper for Python to Verilog conversion
    """
    return convert_generator_debug(func, optimization_level)[0]


def convert_generator_debug(func: ast.FunctionDef, optimization_level: int):
    """
    Wrapper for Python to Verilog conversion
    """
    ir, context = Generator2Graph(func).results
    if optimization_level > 0:
        OptimizeGraph(ir, threshold=optimization_level - 1)
    return verilog.CodeGen(ir, context), ir


def parse_python(code: str, function_name: str, file_path: Optional[str] = None):
    """
    Parses python code into the function and testbench
    """
    assert_type(code, str)
    assert_type(function_name, str)

    def get_file_and_line_num(node: ast.AST):
        """
        Gets file and line number
        """
        if file_path:
            string = file_path
        else:
            string = "line"
        string += f":{node.lineno}:{node.end_lineno}"
        return string

    tree = ast.parse(code)

    func: Optional[ast.FunctionDef]
    test_cases = []

    for stmt in tree.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == function_name:
            logging.info(f"Found function at {get_file_and_line_num(stmt)}")
            func = stmt
        elif (
            isinstance(stmt, ast.Assign)
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Name)
            and stmt.value.func.id == function_name
        ):
            logging.info(f"Found test case at {get_file_and_line_num(stmt)}")
            assert len(stmt.value.args) == 1
            assert isinstance(stmt.value.args[0], ast.Tuple)
            tupl = stmt.value.args[0]
            for i, line in enumerate(code.split("\n")):
                if i + 1 == tupl.lineno:  # 1-indexed line numbers
                    test_case = ast.literal_eval(
                        line[tupl.col_offset : tupl.end_col_offset]
                    )
                    test_cases.append(test_case)
    logging.info(f"Test cases: {test_cases}")

    context = ir.Context(name=function_name)

    input_names = [var.arg for var in func.args.args]
    logging.warning(input_names)

    first_inputs = [val for val in test_cases[0]]
    for case in test_cases:
        for i, (expected, actual) in enumerate(zip(first_inputs, case)):
            assert type(expected) == type(
                actual
            ), f"Expected parameter `{input_names[i]}` to be {type(expected)} but got {type(actual)} instead"
    logging.warning(first_inputs)

    return (func, test_cases)
