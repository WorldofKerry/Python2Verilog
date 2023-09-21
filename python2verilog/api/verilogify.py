"""
Decorators
"""

from __future__ import annotations

import ast
import inspect
import logging
import textwrap
import warnings
from functools import wraps
from types import FunctionType
from typing import Generator, Optional, Protocol, Union, cast

import __main__ as main

from python2verilog import ir
from python2verilog.api.modes import Modes
from python2verilog.api.namespace import get_namespace
from python2verilog.simulation import iverilog
from python2verilog.simulation.display import parse_stdout, strip_signals
from python2verilog.utils.assertions import assert_typed, assert_typed_dict, get_typed
from python2verilog.utils.decorator import decorator_with_args
from python2verilog.utils.fifo import temp_fifo


# pylint: disable=too-many-locals
@decorator_with_args
def verilogify(
    func: FunctionType,
    namespace: Optional[dict[str, ir.Context]] = None,
    optimization_level: int = 1,
    mode: Modes = Modes.OVERWRITE,
):
    """
    :param namespace: the namespace to put this function, for linking purposes
    :param mode: if WRITE or OVERWRITE, files will be written to the specified paths
    """
    get_typed(func, FunctionType)
    assert_typed(mode, Modes)

    if not hasattr(main, "__file__") and namespace is None:
        # No way to query caller filename in IPython / Jupyter notebook
        raise RuntimeError(
            f"{verilogify.__name__}: parameter `{f'{namespace=}'.partition('=')[0]}`"
            f" is required in IPython / Jupyter notebook instances"
        )

    # Get caller filename for default output paths
    # .stack()[2] as this function uses a decorator, so the first frames' filename
    # is the filename that contains that decorator
    filename = inspect.stack()[2].filename

    if namespace is None:
        namespace = get_namespace(filename)
    assert_typed_dict(namespace, str, ir.Context)  # type: ignore[misc]

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
                context.check_output_types(result)

        return func(*args, **kwargs)

    @wraps(func)
    def function_wrapper(*_0, **_1):
        raise TypeError(
            "Non-generator functions currently not supported, "
            "make sure your function has at least one `yield` statement"
        )

    wrapper = (
        generator_wrapper if inspect.isgeneratorfunction(func) else function_wrapper
    )
    wrapper._python2verilog_context = context  # type: ignore # pylint: disable=protected-access
    wrapper._python2verilog_original_func = func  # type: ignore # pylint: disable=protected-access
    namespace[wrapper.__name__] = context
    return wrapper


def get_context(verilogified: FunctionType) -> ir.Context:
    """
    Gets context from verilogified function
    """
    return verilogified._python2verilog_context  # type: ignore # pylint: disable=protected-access


def get_original_func(verilogified: FunctionType) -> FunctionType:
    """
    Gets original function from verilogified function
    """
    return verilogified._python2verilog_original_func  # type: ignore # pylint: disable=protected-access


def get_expected(verilogified: FunctionType) -> Generator[tuple[int, ...], None, None]:
    """
    Get expected output of testbench
    """
    generator_func = get_original_func(verilogified)
    for test in get_context(verilogified).test_cases:
        yield from generator_func(*test)


def get_actual(
    verilogified: FunctionType,
    module: str,
    testbench: str,
    timeout: Optional[int] = None,
) -> Generator[Union[tuple[int, ...], int], None, None]:
    """
    Get expected output of testbench
    """
    context = get_context(verilogified)
    with temp_fifo() as module_fifo, temp_fifo() as tb_fifo:
        stdout, err = iverilog.run_with_fifos(
            context.testbench_name,
            {module_fifo: module, tb_fifo: testbench},
            timeout=timeout,
        )
        assert not err, f"{stdout} {err}"
        yield from strip_signals(parse_stdout(stdout))
