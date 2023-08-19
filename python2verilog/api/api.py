"""
Wrappers
"""

import argparse
import copy
import logging
import os
import ast
import warnings
from typing import Optional, overload

from python2verilog.utils.assertions import assert_type
from ..frontend import Generator2Graph
from .. import ir
from ..backend import verilog
from ..optimizer import OptimizeGraph


@overload
def convert(context: str, code: str, optimization_level: int = 1):
    ...


@overload
def convert(context: ir.Context, code: str, optimization_level: int = 1):
    ...


def convert(context: str | ir.Context, code: str, optimization_level: int = 1):
    """
    Converts python code to verilog module and testbench
    """
    code_gen, _ = convert_to_verilog_ir(context, code, optimization_level)
    return code_gen.get_module_str(), code_gen.new_testbench_str(
        code_gen.context.test_cases
    )


def convert_file_to_file(
    function_name: str,
    input_path: str,
    output_module_path: Optional[str] = None,
    output_testbench_path: Optional[str] = None,
    overwrite: bool = False,
    optimization_level: int = 1,
):
    """
    Reads a python file and outputs verilog and testbench to files
    Default output naming is [python file name stem]_module.sv and [python file name stem]_tb.sv respectively
    """
    python_file_stem = os.path.splitext(input_path)[0]
    if not output_module_path:
        output_module_path = python_file_stem + "_module.sv"
    if not output_testbench_path:
        output_testbench_path = python_file_stem + "_tb.sv"

    with open(input_path, mode="r", encoding="utf8") as python_file:
        module, testbench = convert(
            function_name, python_file.read(), optimization_level
        )

        mode = "w" if overwrite else "x"

        with open(output_module_path, mode=mode, encoding="utf8") as module_file:
            module_file.write(module)

        with open(output_testbench_path, mode=mode, encoding="utf8") as testbench_file:
            testbench_file.write(testbench)


def convert_to_verilog_ir(
    context: str | ir.Context, code: str, optimization_level: int = 1
):
    """
    For more complex usage
    """
    if isinstance(context, str):
        context = ir.Context(name=context)
    return convert_for_debug(
        code=code, context=context, optimization_level=optimization_level
    )


def convert_for_debug(code: str, context: ir.Context, optimization_level: int):
    """
    Converts python code to verilog and its ir
    """
    basic_context, func_ast, func_callable = parse_python(
        code, context.name, extra_test_cases=context.test_cases
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

    test_cases = extra_test_cases if extra_test_cases else []

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
    lines = code.splitlines()
    func_lines = lines[generator_ast.lineno - 1 : generator_ast.end_lineno]
    func_str = "\n".join(func_lines)
    logging.error(func_str)
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
                ), f"Expected parameter `{input_names[i]}` to be {expected_type} but got {type(actual_value)} instead"

    context = ir.Context(name=function_name)

    if initialized:
        logging.info(f"Output param types: {output_types}")
        context.output_vars = [ir.Var(str(i)) for i in range(len(output_types))]

    context.input_vars = [ir.Var(name) for name in input_names]
    context.test_cases = test_cases

    # Currently the types are not used
    return (context, generator_ast, generator_func)
