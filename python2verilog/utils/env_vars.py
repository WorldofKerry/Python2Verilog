"""
Special env variable functions
"""

import os

DEBUG_MODE_ENV_VAR = "PYTHON_2_VERILOG_DEBUG"


def set_debug_mode(mode: bool):
    """
    Sets the debug mode of package
    """
    if mode:
        os.environ[DEBUG_MODE_ENV_VAR] = ""
    else:
        del os.environ[DEBUG_MODE_ENV_VAR]


def is_debug_mode():
    """
    :return: True if in debug mode, false otherwise
    """
    return os.getenv(DEBUG_MODE_ENV_VAR) is not None
