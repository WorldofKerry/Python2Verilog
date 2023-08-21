import os
import warnings


DEBUG_MODE_ENV_VAR = "PYTHON_2_VERILOG_DEBUG"


def set_debug_mode(mode: bool):
    if mode:
        os.environ[DEBUG_MODE_ENV_VAR] = ""
    else:
        del os.environ[DEBUG_MODE_ENV_VAR]


def get_debug_mode():
    return os.getenv(DEBUG_MODE_ENV_VAR) is not None
