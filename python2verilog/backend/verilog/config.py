"""
Configurations
"""

from dataclasses import dataclass

from python2verilog.utils import env


@dataclass
class TestbenchConfig:
    """
    Configurations for test bench code generator
    """

    # Enable random ready signal (for testing correctness)
    random_ready: bool = False


@dataclass
class CodegenConfig(TestbenchConfig):
    """
    Configurations for code generator
    """

    # Enable debug comments graph elements as comment
    add_debug_comments: bool = False

    def __post_init__(self):
        self.add_debug_comments |= bool(env.get_var(env.Vars.DEBUG_COMMENTS))
