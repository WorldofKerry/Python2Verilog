"""
API wrappers
"""

from .text import (
    text_to_context,
    text_to_verilog,
    text_to_text,
)

from .decorator import (
    global_namespace,
    verilogify,
    new_namespace,
    verilogify_namespace,
    verilogify_function,
)

from .wrappers import context_to_verilog
