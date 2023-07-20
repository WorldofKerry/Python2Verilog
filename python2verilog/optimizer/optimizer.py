"""
Optimizer algorithms that operate ontop of the intermediate representation
"""

import typing
import warnings
import random

from .. import ir


def replace_single_case(node: ir.Statement):
    """
    Replaces single-case case statements with a regular statement

    Excludes the root even if it may be a case statement

    Note: doesn't affect performance
    """

    def check_caseitems(node: ir.CaseItem):
        """
        Checks if a case item contains a Case with one CaseItem,
        then replaces it with a statement
        Note: currently doesnt remove no-longer-needed state variables
        TODO: fix above note
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

    Performance: a clock cycle is saved per if-else statement cycle
    """
    if isinstance(node, ir.IfElseWrapper):
        assert isinstance(node.case_items[0].statements[0], ir.IfElse)
        node.case_items[0].statements[0].then_body += node.case_items[1].statements
        node.case_items[0].statements[0].else_body += node.case_items[2].statements
    if isinstance(node, ir.Case):
        for item in node.case_items:
            for stmt in item.statements:
                optimize_if(stmt)
    return node


def combine_cases(_: ir.Statement):
    """
    Looks at a case item.

    Combines it with all subsequent case items if
    subsequent case items' rvalues do not depend on any lvalues of prior case items

    """
