"""
Optimizer algorithms that operate ontop of the intermediate representation
"""

import warnings
from .. import ir


def replace_single_case(node: ir.Statement):
    """
    Replaces single-case case statements with a regular statement

    Circle Lines is a good test case with its else block
    """
    if not node:
        return
    if isinstance(node, ir.Case):
        warnings.warn("Found Case!")
