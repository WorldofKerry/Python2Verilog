"""
Configurations
"""

from dataclasses import dataclass


@dataclass
class CodegenConfig:
    """
    Configurations
    """

    # Enable random ready signal in testbench
    random_ready: bool = False
