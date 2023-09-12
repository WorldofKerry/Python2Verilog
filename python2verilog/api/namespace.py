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
file_namespaces: dict[Path, dict[str, ir.Context]] = {}


def get_namespace(path: Path | str) -> dict[str, ir.Context]:
    """
    Get namespace of a file and creates it if it doesn't exist

    Only the path without extension is used, e.g.,

    - `/path/to/file` -> `/path/to/file` namespace
    - `/path/to/file.py` -> `/path/to/file` same namespace as above
    - `/path/to/file.ext` -> `/path/to/file` same namespace as above
    """
    path = Path(path)
    namespace = path.with_suffix("")
    if namespace not in file_namespaces:
        file_namespaces[namespace] = {}
    return file_namespaces[namespace]


def new_namespace(path: Path | str) -> dict[str, ir.Context]:
    """
    Create a new namespace for path
    """
    path = Path(path)
    namespace = path.with_suffix("")
    assert namespace not in file_namespaces, f"Namespace for {namespace} already exists"
    return get_namespace(namespace)


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
