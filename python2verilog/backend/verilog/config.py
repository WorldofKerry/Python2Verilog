"""
Configurations
"""

from dataclasses import dataclass, field

from python2verilog.utils import env


@dataclass(frozen=True)
class TestbenchConfig:
    """
    Configurations for test bench code generator
    """

    # Enable random ready signal (for testing correctness)
    random_ready: bool = False


@dataclass(frozen=True)
class CodegenConfig(TestbenchConfig):
    """
    Configurations for code generator
    """

    # Enable debug comments graph elements as comment
    add_debug_comments: bool = field(
        default_factory=lambda: bool(env.get_var(env.Vars.DEBUG_COMMENTS))
    )

    # def __post_init__(self):
    #     self.add_debug_comments |= bool(env.get_var(env.Vars.DEBUG_COMMENTS))

    # def __hash__(self):
    #     return hash(self.__dict__)
