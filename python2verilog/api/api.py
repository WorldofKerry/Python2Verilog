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

# All functions if a lesser namespace is not given
global_scope: dict[FunctionType, ir.Context] = {}
namespaces = [global_scope]


def new_scope():
    """
    Create new namespace and returns that namespace
    """
    namespace = {}
    namespaces.append(namespace)
    return namespace


def __scope_exit_handler():
    """
    Handles the conversions in each namespace for program exit
    """
    for namespace in namespaces:
        for _, value in namespace.items():
            print(value.name, value.test_cases, value.input_types, value.output_types)
        for context in namespace.values():
            ir_root, context = Generator2Graph(context, context.py_ast).results
            if context.optimization_level > 0:
                OptimizeGraph(ir_root, threshold=context.optimization_level - 1)
            ver_code_gen = verilog.CodeGen(ir_root, context)
            assert isinstance(context, ir.Context)

            if context.write:
                module_str = ver_code_gen.get_module_str()
                tb_str = ver_code_gen.new_testbench_str(context.test_cases)
                context.module_file.write(module_str)
                context.testbench_file.write(tb_str)


atexit.register(__scope_exit_handler)


# pylint: disable=dangerous-default-value
@decorator_with_args
def verilogify(
    func: FunctionType,
    namespace: dict[FunctionType, ir.Context] = global_scope,
    module_output: Optional[Union[os.PathLike, typing.IO]] = None,
    testbench_output: Optional[Union[os.PathLike, typing.IO]] = None,
    write: bool = False,
    overwrite: bool = False,
):
    """
    :param namespace: the namespace to put this function, for linking purposes
    :param write: if True, files will be written to the specified paths
    :param overwrite: If True, existing files will be overwritten
    :param module_output: path to write verilog module to, defaults to function_name.sv
    :param testbench_output: path to write verilog testbench to, defaults to function_name_tb.sv
    """
    if overwrite and not write:
        raise RuntimeError("Overwrite is true, but write is set to false")
    if func in namespace:
        raise RuntimeError(f"{func.__name__} has already been decorated")

    # Get caller filename for default output paths
    # .stack()[2] as this function uses a decorator, so the first frames' filename
    # is the filename that contains that decorator
    filename = inspect.stack()[2].filename
    input_file_stem = os.path.splitext(filename)[0]  # path with no extension

    if not module_output:
        module_output = Path(input_file_stem + ".sv")
    if not testbench_output:
        testbench_output = Path(input_file_stem + "_tb.sv")

    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    assert len(tree.body) == 1
    func_ast = tree.body[0]
    assert isinstance(
        func_ast, ast.FunctionDef
    ), f"Got {type(func_ast)} expected {ast.FunctionDef}"

    context = ir.Context(name=func.__name__)
    context.py_ast = func_ast
    context.py_func = func

    context.write = write
    context.overwrite = overwrite

    if write:
        if overwrite:
            mode = "w"
        else:
            mode = "x"
        # pylint: disable=consider-using-with
        if isinstance(module_output, os.PathLike):
            module_output = open(module_output, mode=mode, encoding="utf8")
        if isinstance(testbench_output, os.PathLike):
            testbench_output = open(testbench_output, mode=mode, encoding="utf8")
        context.module_file = module_output
        context.testbench_file = testbench_output

    namespace[func] = context

    @wraps(func)
    def generator_wrapper(*args, **kwargs):
        if kwargs:
            raise RuntimeError(
                "Keyword arguments not yet supported, use positional arguments only"
            )
        context = namespace[func]
        context.test_cases.append(args)
        if not context.input_types:
            context.input_types = [type(arg) for arg in args]
        else:
            context.check_input_types(args)

        for result in func(*args, **kwargs):
            if not isinstance(result, tuple):
                result = (result,)

            if not context.output_types:
                logging.error(f"Using {result} as reference")
                context.output_types = [type(arg) for arg in result]
            else:
                logging.error(f"Next yield gave {result}")
                context.check_output_types(result)

        return func

    @wraps(func)
    def function_wrapper(*args, **kwargs):
        logging.error("Non-generator functions currently not supported")
        return func(*args, **kwargs)

    return generator_wrapper if inspect.isgeneratorfunction(func) else function_wrapper


@overload
def convert(context: str, code: str, optimization_level: int = 1):
    ...


@overload
def convert(context: ir.Context, code: str, optimization_level: int = 1):
    ...


def convert(context: Union[str, ir.Context], code: str, optimization_level: int = 1):
    """
    Converts python code to verilog module and testbench
    """
    if isinstance(context, str):
        context = ir.Context(name=context)
    ver_code_gen, _ = convert_for_debug(
        code=code, context=context, optimization_level=optimization_level
    )
    return ver_code_gen.get_module_str(), ver_code_gen.new_testbench_str(
        context.test_cases
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
    Default output naming is [python file name stem]_module.sv
    and [python file name stem]_tb.sv respectively
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


def convert_for_debug(
    code: str, context: Union[str, ir.Context], optimization_level: int
):
    """
    Converts python code to verilog and its ir
    """
    if isinstance(context, str):
        context = ir.Context(name=context)

    _context, func_ast, _ = parse_python(
        code, context.name, extra_test_cases=context.test_cases
    )
    ir_root, _context = Generator2Graph(_context, func_ast).results
    if optimization_level > 0:
        OptimizeGraph(ir_root, threshold=optimization_level - 1)
    return verilog.CodeGen(ir_root, _context), ir_root


def parse_python(
    code: str,
    function_name: str,
    file_path: Optional[str] = None,
    extra_test_cases: Optional[list] = None,
):
    """
    Parses python code into the function and testbench
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
        logging.info(f"Output param types: {output_types}")
        context.output_vars = [ir.Var(str(i)) for i in range(len(output_types))]

    context.input_vars = [ir.Var(name) for name in input_names]
    context.test_cases = test_cases

    # Currently the types are not used
    return (context, generator_ast, generator_func)
