"""
Python 2 Verilog
"""
import importlib.metadata

__version__ = importlib.metadata.version("python2verilog")

from .api import (
    Modes,
    context_to_verilog,
    get_actual_raw,
    get_context,
    get_expected,
    get_namespace,
    get_original_func,
    namespace_to_file,
    namespace_to_verilog,
    new_namespace,
    py_to_verilog,
    verilogify,
)
