"""
Special env variable functions
"""

import logging
import os
from enum import Enum
from typing import Optional

PREFIX = "PYTHON_2_VERILOG_"


class Vars(Enum):
    """
    Env var names
    """

    DEBUG_MODE = PREFIX + "DEBUG"
    IVERILOG_PATH = PREFIX + "IVERILOG_PATH"
    IS_SYSTEM_VERILOG = PREFIX + "SYSTEM_VERILOG"


def set_debug_mode(mode: bool):
    """
    Sets the debug mode of package
    """
    if mode:
        set_var(Vars.DEBUG_MODE, "")
    else:
        set_var(Vars.DEBUG_MODE, None)


def is_debug_mode():
    """
    :return: True if in debug mode, false otherwise
    """
    return get_var(Vars.DEBUG_MODE) is not None


def set_var(name: Vars, value: Optional[str]):
    """
    Set an env var
    """
    assert isinstance(name, Vars)
    assert isinstance(value, (type(None), str))
    if value is not None:
        os.environ[str(name)] = value
    else:
        try:
            del os.environ[str(name)]
        except KeyError:
            pass


def get_var(name: Vars):
    """
    Get an env var
    """
    assert isinstance(name, Vars)
    return os.getenv(str(name))
