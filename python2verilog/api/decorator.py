"""
Decorators
"""

import atexit
import io
import logging
import os
import ast
import textwrap
import typing
from pathlib import Path
from typing import Callable, Optional, Union
from functools import wraps
import inspect
from types import FunctionType
from python2verilog.api.wrappers import context_to_verilog

from python2verilog.utils.assertions import assert_dict_type, assert_type
from python2verilog.utils.decorator import decorator_with_args
from .. import ir

# All functions if a lesser namespace is not given
global_namespace: dict[Callable, ir.Context] = {}
exit_namespaces = [global_namespace]


def new_namespace():
    """
    Create new namespace that is handled on program exit

    :return: newly created namespace
    """
    namespace = {}
    exit_namespaces.append(namespace)
    return namespace


def verilogify_function(context: ir.Context):
    """
    Verilogifies a function that has be decorated

    If decorated with write enabled, writes to designated files/streams

    :return: (module, testbench) tuple
    """
    assert_type(context, ir.Context)
    ver_code_gen, _ = context_to_verilog(context)

    module_str = ver_code_gen.get_module_str()
    tb_str = ver_code_gen.get_testbench_str()
    if context.write:
        context.module_file.write(module_str)
        context.testbench_file.write(tb_str)

    return (module_str, tb_str)


def verilogify_namespace(namespace: dict[Callable, ir.Context]):
    """
    Verilogifies a namespace
    """
    logging.info(verilogify_namespace.__name__)
    for context in namespace.values():
        _ = verilogify_function(context=context)
        logging.info(
            context.name, context.test_cases, context.input_types, context.output_types
        )


def __global_namespace_exit_handler():
    """
    Handles the conversions in each namespace for program exit
    """
    for namespace in exit_namespaces:
        verilogify_namespace(namespace)


atexit.register(__global_namespace_exit_handler)


def get_func_ast_from_func(func: FunctionType):
    """
    Given a function, gets its ast

    :return: ast rooted at function
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    assert len(tree.body) == 1

    func_tree = tree.body[0]
    assert isinstance(
        func_tree, ast.FunctionDef
    ), f"Got {type(func_tree)} expected {ast.FunctionDef}"

    return func_tree


# pylint: disable=dangerous-default-value
# pylint: disable=too-many-locals
@decorator_with_args
def verilogify(
    func: FunctionType,
    namespace: dict[Callable, ir.Context] = global_namespace,
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
    assert_type(func, FunctionType)
    assert_dict_type(namespace, Callable, ir.Context)
    assert_type(module_output, (os.PathLike, io.IOBase))
    assert_type(testbench_output, (os.PathLike, io.IOBase))
    assert_type(write, bool)
    assert_type(overwrite, bool)

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

    context.input_vars = [ir.Var(name.arg) for name in func_ast.args.args]

    context.write = write

    if write:
        mode = "w" if overwrite else "x"

        # pylint: disable=consider-using-with
        if isinstance(module_output, os.PathLike):
            try:
                module_output = open(module_output, mode=mode, encoding="utf8")
            except FileExistsError as e:
                raise FileExistsError("Try setting overwrite to True") from e
        if isinstance(testbench_output, os.PathLike):
            try:
                testbench_output = open(testbench_output, mode=mode, encoding="utf8")
            except FileExistsError as e:
                raise FileExistsError("Try setting overwrite to True") from e

        context.module_file = module_output
        context.testbench_file = testbench_output

    @wraps(func)
    def generator_wrapper(*args, **kwargs):
        nonlocal context
        if kwargs:
            raise RuntimeError(
                "Keyword arguments not yet supported, use positional arguments only"
            )
        context.test_cases.append(args)
        if not context.input_types:
            context.input_types = [type(arg) for arg in args]
        else:
            context.check_input_types(args)

        for result in func(*args, **kwargs):
            if not isinstance(result, tuple):
                result = (result,)

            if not context.output_types:
                logging.info(f"Using {result} as reference")
                context.output_types = [type(arg) for arg in result]
                context.default_output_vars()
            else:
                logging.debug(f"Next yield gave {result}")
                context.check_output_types(result)

        return func(*args, **kwargs)

    @wraps(func)
    def function_wrapper(*args, **kwargs):
        logging.error("Non-generator functions currently not supported")
        return func(*args, **kwargs)

    wrapper = (
        generator_wrapper if inspect.isgeneratorfunction(func) else function_wrapper
    )
    namespace[wrapper] = context
    return wrapper
