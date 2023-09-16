"""
Handles namespaces
"""

from __future__ import annotations

from typing import Any, Callable

from python2verilog.api.file_namespaces import file_namespaces
from python2verilog.api.namespace import namespace_to_file

try:
    # For iPython
    def _exit_register(fun: Callable[[], Any], *_args, **_kwargs):
        """Decorator that registers at post_execute. After its execution it
        unregisters itself for subsequent runs."""

        def callback():
            fun()
            ip.events.unregister("post_execute", callback)

        ip.events.register("post_execute", callback)

    ip = get_ipython()  # type: ignore

except NameError:
    # For normal
    from atexit import register as _exit_register  # type: ignore


@_exit_register
def __namespace_exit_handler():
    """
    Handles the conversions in each namespace for program exit
    """
    # print("exit handler")
    for stem, namespace in file_namespaces.items():
        # print(stem, namespace)
        namespace_to_file(stem, namespace)
