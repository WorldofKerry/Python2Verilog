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
            func_call_str = ast.get_source_segment(code, stmt.value)
            assert func_call_str
            func_call_str = "(" + func_call_str.split("(", 1)[1]
            func_call_str = func_call_str.rsplit(")", 1)[0] + ")"

            test_case = ast.literal_eval(func_call_str)
            test_cases.append(test_case)

            logging.info(
                f"Found test case at {get_file_and_line_num(stmt)} with {test_case}"
            )

    logging.info(f"Test cases: {test_cases}")

    input_names = [var.arg for var in func.args.args]
    logging.info(f"Input param names: {input_names}")

    input_types = [type(val) for val in test_cases[0]]
    for tupl in test_cases:
        for i, (expected_type, actual_value) in enumerate(zip(input_types, tupl)):
            assert expected_type == type(
                actual_value
            ), f"Expected parameter `{input_names[i]}` to be {expected_type} but got {type(actual_value)} instead"
    logging.info(f"Input param types: {input_types}")

    locals_ = dict()
    exec(code, None, locals_)  # 1-indexed
    # Note that only first test case is used
    generator_func = locals_[function_name]

    initialized = False

    for test_case in test_cases:
        generator = generator_func(*test_case)

        if not initialized:
            output_types = [type(val) for val in next(generator)]
            initialized = True

        for tupl in generator:
            for i, (expected_type, actual_value) in enumerate(zip(input_types, tupl)):
                assert expected_type == type(
                    actual_value
                ), f"Expected parameter `{input_names[i]}` to be {expected_type} but got {type(actual_value)} instead"

    logging.info(f"Output param types: {output_types}")

    context = ir.Context(name=function_name)
    context.input_vars = [ir.Var(name) for name in input_names]
    context.output_vars = [ir.Var(str(i)) for i in range(len(output_types))]

    # Currently the types are not used
    return (func, test_cases, context)
