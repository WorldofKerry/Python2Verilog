"""
Optimizer algorithms that operate ontop of the intermediate representation
"""

import warnings
from .. import ir


def optimize(node: ir.Statement, _: ir.Context):
    """
    Optimizes node by mutating it
    """
    replace_single_case(node)
    return node


def replace_single_case(node: ir.Statement):
    """
    Replaces single-case case statements with a regular statement

    Circle Lines is a good test case with its else block
    """
    if not node:
        return node
    if isinstance(node, ir.Case):
        warnings.warn("Found Case!")
    return node
