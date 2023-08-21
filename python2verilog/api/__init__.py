"""
API wrappers
"""

from .cli import (
    parse_python,
    convert_for_debug,
    convert,
    convert_file_to_file,
)

from .decorator import (
    global_namespace,
    verilogify,
    new_namespace,
    verilogify_namespace,
    verilogify_function,
)
