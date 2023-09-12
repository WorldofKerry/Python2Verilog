"""
Handles namespaces
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from python2verilog import ir
from python2verilog.api.modes import Modes
from python2verilog.api.wrappers import context_to_text_and_file
from python2verilog.utils.assertions import assert_typed, assert_typed_dict, get_typed
from python2verilog.utils.decorator import decorator_with_args

try:
    # For iPython
    def exit_register(fun: Callable[[], Any], *_args, **_kwargs):
        """Decorator that registers at post_execute. After its execution it
        unregisters itself for subsequent runs."""

        def callback():
            fun()
            ip.events.unregister("post_execute", callback)

        ip.events.register("post_execute", callback)

    ip = get_ipython()  # type: ignore

except NameError:
    # For normal
    from atexit import register as exit_register  # type: ignore

# All functions if a lesser namespace is not given
exit_namespaces: list[dict[str, ir.Context]] = []
file_namespaces: dict[Path, dict[str, ir.Context]] = {}


def get_file_namespace(path: Path | str):
    """
    Get file namespace of specific file
    """
    print(path)
    path = Path(path)
    if path not in file_namespaces:
        file_namespaces[path] = {}
    return file_namespaces[path]


def new_namespace() -> dict[str, ir.Context]:
    """
    Create new namespace that is handled on program exit

    :return: newly created namespace
    """
    namespace: dict[str, ir.Context] = {}
    exit_namespaces.append(namespace)
    return namespace


def namespace_to_file(namespace: dict[str, ir.Context]):
    """
    Verilogifies a namespace
    """
    logging.info(namespace_to_file.__name__)
    for context in namespace.values():
        _ = context_to_text_and_file(context=context)
        logging.info(
            context.name, context.test_cases, context.input_types, context.output_types
        )


@exit_register
def __namespace_exit_handler():
    """
    Handles the conversions in each namespace for program exit
    """
    for namespace in file_namespaces.values():
        namespace_to_file(namespace)
    for namespace in exit_namespaces:
        namespace_to_file(namespace)
