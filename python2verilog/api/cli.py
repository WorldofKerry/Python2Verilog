"""
Wrappers
"""

import argparse
import atexit
import copy
from io import IOBase
import logging
import os
import ast
import textwrap
import types
import typing
import warnings
from pathlib import Path
from typing import Optional, Union, overload
from functools import wraps
import inspect
from types import FunctionType

from python2verilog.utils.assertions import assert_type
from python2verilog.utils.decorator import decorator_with_args
from ..frontend import Generator2Graph
from .. import ir
from ..backend import verilog
from ..optimizer import OptimizeGraph


def convert_from_cli(
    code: str,
    func_name: str,
    optimization_level: int,
    test_cases: Optional[list] = None,
    file_path: str = "",
):
    """
    Converts from cli
    """
    context = parse_python(
        code=code,
        function_name=func_name,
        extra_test_cases=test_cases,
        file_path=file_path,
    )
    assert isinstance(context, ir.Context)
    assert isinstance(test_cases, list)
    context.test_cases = test_cases
    context.validate()

    ir_root, context = Generator2Graph(context, context.py_ast).results
    if optimization_level > 0:
        OptimizeGraph(ir_root, threshold=optimization_level - 1)
    return verilog.CodeGen(ir_root, context), ir_root


def convert_for_debug(
    code: str,
    optimization_level: int,
    test_cases: list[tuple],
    name: str,
):
    """
    Converts python code to verilog and its ir
    """
    context = parse_python(code=code, function_name=name, extra_test_cases=test_cases)
    ir_root, context = Generator2Graph(context, context.py_ast).results
    if optimization_level > 0:
        OptimizeGraph(ir_root, threshold=optimization_level - 1)
    return verilog.CodeGen(ir_root, context), ir_root


def parse_python(
    code: str,
    function_name: str,
    file_path: Optional[str] = None,
    extra_test_cases: Optional[list] = None,
):
    """
    Parses python code into the function and testbench

    :return: validated context
    """
    # pylint: disable=too-many-locals
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
        string += f":{node.lineno}"
        return string

    tree = ast.parse(code)

    test_cases = extra_test_cases if extra_test_cases else []
    print(f"parse_python test cases {test_cases}")

    for node in ast.walk(tree):
        logging.debug(f"Walking through {ast.dump(node)}")
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            logging.info(f"Found function at {get_file_and_line_num(node)}")
            generator_ast = node
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == function_name
        ):
            func_call_str = ast.get_source_segment(code, node)
            assert func_call_str
            func_call_str = "(" + func_call_str.split("(", 1)[1]
            func_call_str = func_call_str.rsplit(")", 1)[0] + ")"

            test_case = ast.literal_eval(func_call_str)
            if not isinstance(test_case, tuple):
                test_case = (test_case,)
            test_cases.append(test_case)

            logging.info(
                f"Found test case at {get_file_and_line_num(node)} with {test_case}"
            )

    logging.info(f"Test cases: {test_cases}")

    try:
        input_names = [var.arg for var in generator_ast.args.args]
    except UnboundLocalError as e:
        raise RuntimeError(f"Didn't find `{function_name}` in file") from e

    logging.info(f"Input param names: {input_names}")

    initialized = False
    input_types: Union[str, list] = "Unknown"
    for test_case in test_cases:
        if not initialized:
            input_types = [type(val) for val in test_case]
            initialized = True

        for i, (expected_type, actual_value) in enumerate(zip(input_types, test_case)):
            assert expected_type == type(
                actual_value
            ), f"Expected parameter `{input_names[i]}` to be \
                {expected_type} but got {type(actual_value)} instead"

    logging.info(f"Input param types: {input_types}")

    locals_: dict[str, FunctionType] = {}
    lines = code.splitlines()
    func_lines = lines[generator_ast.lineno - 1 : generator_ast.end_lineno]
    func_str = "\n".join(func_lines)
    logging.debug(func_str)
    exec(func_str, None, locals_)
    try:
        generator_func = locals_[function_name]
    except KeyError as e:
        raise RuntimeError(f"def {function_name} not found in global context") from e

    initialized = False

    for test_case in test_cases:
        generator = generator_func(*test_case)

        if not initialized:
            result = next(generator)
            if not isinstance(result, tuple):
                result = (result,)
            output_types = [type(val) for val in result]
            initialized = True

        for test_case in generator:
            if not isinstance(test_case, tuple):
                test_case = (test_case,)

            for i, (expected_type, actual_value) in enumerate(
                zip(input_types, test_case)
            ):
                assert expected_type == type(
                    actual_value
                ), f"Expected parameter `{input_names[i]}` to be \
                    {expected_type} but got {type(actual_value)} instead"

    context = ir.Context(name=function_name)

    if initialized:
        context.output_types = output_types
        context.default_output_vars()

    logging.info(f"Output param types: {context.output_types}")
    logging.info(f"Output param names: {context.output_vars}")

    context.input_vars = [ir.Var(name) for name in input_names]
    assert isinstance(input_types, list)
    context.input_types = input_types
    context.test_cases = test_cases
    context.py_ast = generator_ast
    context.py_func = generator_func

    # Currently the types are not used
    return context.validate()
