"""
Decorators
"""

from __future__ import annotations

import ast
import inspect
import logging
import textwrap
from functools import wraps
from types import FunctionType
from typing import Optional

from python2verilog import ir
from python2verilog.api.modes import Modes
from python2verilog.api.namespace import get_namespace
from python2verilog.utils.assertions import assert_typed, assert_typed_dict, get_typed
from python2verilog.utils.decorator import decorator_with_args


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


# pylint: disable=too-many-locals
@decorator_with_args
def verilogify(
    func: FunctionType,
    namespace: Optional[dict[str, ir.Context]] = None,
    optimization_level: int = 1,
    mode: Modes = Modes.NO_WRITE,
):
    """
    :param namespace: the namespace to put this function, for linking purposes
    :param mode: if WRITE or OVERWRITE, files will be written to the specified paths
    """
    get_typed(func, FunctionType)
    assert_typed(mode, Modes)

    # Get caller filename for default output paths
    # .stack()[2] as this function uses a decorator, so the first frames' filename
    # is the filename that contains that decorator
    filename = inspect.stack()[2].filename

    if namespace is None:
        namespace = get_namespace(filename)
    assert_typed_dict(namespace, str, ir.Context)  # type: ignore[misc]

    if func.__name__ in namespace:
        raise RuntimeError(f"{func.__name__} has already been decorated")

    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    assert len(tree.body) == 1
    func_ast = tree.body[0]
    assert isinstance(
        func_ast, ast.FunctionDef
    ), f"Got {type(func_ast)} expected {ast.FunctionDef}"

    context = ir.Context(name=func.__name__)
    context.py_ast = func_ast
    context.py_func = func
    context.py_string = inspect.getsource(func)

    context.input_vars = [ir.Var(name.arg) for name in func_ast.args.args]

    context.mode = mode
    context.optimization_level = optimization_level

    context.namespace = namespace

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
    namespace[wrapper.__name__] = context
    return wrapper