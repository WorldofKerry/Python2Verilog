"""
Special env variable functions
"""

import logging
import os
from enum import Enum
from types import NoneType
from typing import Optional


class Vars(Enum):
    """
    Env var names
    """

    DEBUG_MODE = "PYTHON_2_VERILOG_DEBUG"
    IVERILOG_PATH = "PYTHON_2_VERILOG_IVERILOG_PATH"


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
    assert isinstance(value, (NoneType, str))
    if value is not None:
        os.environ[str(name)] = value
    else:
        del os.environ[str(name)]


def get_var(name: Vars):
    """
    Get an env var
    """
    assert isinstance(name, Vars)
    logging.debug(f"Get {name}")
    return os.getenv(str(name))
