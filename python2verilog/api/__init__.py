"""
API wrappers
"""

from .decorator import (
    global_namespace,
    new_namespace,
    verilogify,
    verilogify_function,
    verilogify_namespace,
)
from .wrappers import context_to_verilog, text_to_context, text_to_text, text_to_verilog
