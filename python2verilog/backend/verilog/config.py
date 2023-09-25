"""
Configurations
"""

from dataclasses import dataclass


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
