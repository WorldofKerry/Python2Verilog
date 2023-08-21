"""
API wrappers
"""

from .cli import (
    parse_python,
    convert_for_debug,
)

from .decorator import (
    global_namespace,
    verilogify,
    new_namespace,
    verilogify_namespace,
    verilogify_function,
)
