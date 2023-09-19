"""
API wrappers
"""


from . import exit_handler  # otherwise file is not loaded
from .from_context import (
    context_to_codegen,
    context_to_verilog,
    context_to_verilog_and_dump,
)
from .from_text import py_to_codegen, py_to_context, py_to_verilog
from .modes import Modes
from .namespace import (
    get_namespace,
    namespace_to_file,
    namespace_to_verilog,
    new_namespace,
)
from .verilogify import (
    get_actual,
    get_context,
    get_expected,
    get_original_func,
    verilogify,
)
