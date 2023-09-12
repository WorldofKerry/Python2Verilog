"""
Handles namespaces
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from python2verilog import ir
from python2verilog.api.file_namespaces import file_namespaces
from python2verilog.api.modes import Modes
from python2verilog.api.wrappers import context_to_text
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


def namespace_to_file(path: Path, namespace: dict[str, ir.Context]):
    """
    Verilogifies a namespace
    """
    logging.info(namespace_to_file.__name__)

    with open(str(path) + ".sv", mode="w", encoding="utf8") as module_file, open(
        str(path) + "_tb.sv", mode="w", encoding="utf8"
    ) as testbench_file:
        for context in namespace.values():
            if Modes.write(context.mode):
                module, testbench = context_to_text(context=context)
                module_file.write(module)
                testbench_file.write(testbench)


@exit_register
def __namespace_exit_handler():
    """
    Handles the conversions in each namespace for program exit
    """
    for stem, namespace in file_namespaces.items():
        namespace_to_file(stem, namespace)
