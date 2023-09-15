"""
Handles namespaces
"""

from __future__ import annotations

import logging
from pathlib import Path

from python2verilog import ir
from python2verilog.api.file_namespaces import file_namespaces
from python2verilog.api.from_context import context_to_text
from python2verilog.api.modes import Modes


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

    Only the path without extension is used, e.g.,

    - `/path/to/file` -> `/path/to/file` namespace
    - `/path/to/file.py` -> `/path/to/file` same namespace as above
    - `/path/to/file.ext` -> `/path/to/file` same namespace as above
    """
    path = Path(path)
    namespace = path.with_suffix("")
    assert namespace not in file_namespaces, f"Namespace for {namespace} already exists"
    return get_namespace(namespace)


def namespace_to_file(path: Path, namespace: dict[str, ir.Context]):
    """
    Namespace to modules and testbneches files
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


def namespace_to_verilog(namespace: dict[str, ir.Context]) -> tuple[str, str]:
    """
    Namespace to modules and testbenches str

    :return: (modules, testbenches)
    """
    module = ""
    testbench = ""
    for context in namespace.values():
        if Modes.write(context.mode):
            mod, tb = context_to_text(context=context)
            module += mod
            testbench += tb
    return module, testbench
