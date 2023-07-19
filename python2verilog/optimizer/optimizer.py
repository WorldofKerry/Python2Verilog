"""
Optimizer algorithms that operate ontop of the intermediate representation
"""
from .. import ir


def replace_single_case(node: ir.Statement):
    """
    Replaces single-case case statements with a regular statement
    """
    if not node:
        return
