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


def convert_generator_debug(
    code: str,
    name: str,
    optimization_level: int,
    extra_test_cases: Optional[list] = None,
):
    """
    Wrapper for Python to Verilog conversion
    """
    basic_context, func_ast, func_callable = parse_python(
        code, name, extra_test_cases=extra_test_cases
    )
    ir_root, context = Generator2Graph(basic_context, func_ast).results
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
        string += f":{node.lineno}"
        return string

    tree = ast.parse(code)

    generator_ast: Optional[ast.FunctionDef]
    test_cases = extra_test_cases if extra_test_cases else []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            logging.info(f"Found function at {get_file_and_line_num(node)}")
            generator_ast = node
        elif (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == function_name
        ):
            func_call_str = ast.get_source_segment(code, node.value)
            assert func_call_str
            func_call_str = "(" + func_call_str.split("(", 1)[1]
            func_call_str = func_call_str.rsplit(")", 1)[0] + ")"

            test_case = ast.literal_eval(func_call_str)
            test_cases.append(test_case)

            logging.info(
                f"Found test case at {get_file_and_line_num(node)} with {test_case}"
            )

    logging.info(f"Test cases: {test_cases}")

    input_names = [var.arg for var in generator_ast.args.args]

    logging.info(f"Input param names: {input_names}")

    initialized = False
    input_types: str | list = "Unknown"
    for test_case in test_cases:
        if not initialized:
            input_types = [type(val) for val in test_case]
            initialized = True

        for i, (expected_type, actual_value) in enumerate(zip(input_types, test_case)):
            assert expected_type == type(
                actual_value
            ), f"Expected parameter `{input_names[i]}` to be {expected_type} but got {type(actual_value)} instead"

    logging.info(f"Input param types: {input_types}")

    locals_ = dict()
    exec(code, None, locals_)
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
                ), f"Expected parameter `{input_names[i]}` to be {expected_type} but got {type(actual_value)} instead"

    context = ir.Context(name=function_name)

    if initialized:
        logging.info(f"Output param types: {output_types}")
        context.output_vars = [ir.Var(str(i)) for i in range(len(output_types))]

    context.input_vars = [ir.Var(name) for name in input_names]
    context.test_cases = test_cases

    # Currently the types are not used
    return (context, generator_ast, generator_func)
