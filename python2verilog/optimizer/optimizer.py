"""
Optimizer algorithms that operate ontop of the intermediate representation
"""

import warnings
import random

from .. import ir


def optimize(node: ir.Statement, _: ir.Context):
    """
    Optimizes node by mutating it
    """
    replace_single_case(node)
    return node


def recurse(node: ir.Statement, func: callable):
    """
    Warning: causes astroid-error on Pylint
    Recurses over types that have bodies
    """
    if not node:
        return
    if isinstance(node, ir.Case):
        for item in node.case_items:
            for stmt in item.statements:
                func(stmt)


def replace_single_case(node: ir.Statement):
    """
    Replaces single-case case statements with a regular statement
    Excludes the root even if it may be a case statement

    Circle Lines is a good test case with its else block
    """

    def check_caseitems(node: ir.CaseItem):
        """
        Checks if a case item contains a Case with one CaseItem,
        then replaces it with a statement
        Note: currently doesnt remove no-longer-needed state variables
        """
        statements = []
        for stmt in node.statements:
            if isinstance(stmt, ir.Case) and len(stmt.case_items) == 1:
                statements += stmt.case_items[0].statements
            else:
                statements.append(stmt)
        return statements

    if not node:
        return node
    if isinstance(node, ir.Case):
        for item in node.case_items:
            item.statements = check_caseitems(item)
            for stmt in item.statements:
                replace_single_case(stmt)
    return node


def optimize_if(node: ir.Statement):
    """
    Avoids a clock cycle waste on an if statement,
    Appends the contents of the next block in the then/else blocks
    """
    # if (
    #     isinstance(node, ir.Case)
    #     and len()
    #     and isinstance(node.case_items[0].statements[0], ir.IfElse)
    # ):
    #     warnings.warn(f"Found IF wrapper {node.to_string()}")
    # if isinstance(node, ir.Case):
    #     for item in node.case_items:
    #         for stmt in item.statements:
    #             optimize_if(stmt)
    # # recurse(node, optimize_if)
    return node
