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

    # Recurse
    if isinstance(node, ir.Case):
        for item in node.case_items:
            for stmt in item.statements:
                optimize_if(stmt)
    return node


def combine_cases(node: ir.Statement):
    """
    Looks at a case item.

    Combines it with all subsequent case items if
    subsequent case items' rvalues do not depend on any lvalues of prior case items

    """

    def grab_vars(expr: ir.Expression, variables: set[str]):
        """
        Gets all vars referenced by expression

        Unless they are a state sub
        """
        if isinstance(expr, ir.Var):
            variables.add(expr.string)
        if isinstance(expr, ir.BinOp):
            grab_vars(expr.left, variables)
            grab_vars(expr.right, variables)

    def analyze_case(node: ir.Case):
        """
        Does the actual combining
        """
        assert isinstance(node, ir.Case)
        lvalues: set[str] = set()
        valid_stmt_count = 0
        item_idx = 0
        while item_idx < len(node.case_items):
            item = node.case_items[item_idx]

            rvalues: set[str] = set()

            stmt_idx = 0
            while stmt_idx < len(item.statements):
                stmt = item.statements[stmt_idx]

                # warnings.warn(f"{stmt.to_string()}")

                if isinstance(stmt, ir.ValidSubsitution):
                    valid_stmt_count += 1

                if isinstance(stmt, ir.NonBlockingSubsitution) and not isinstance(
                    stmt, ir.StateSubsitution
                ):
                    grab_vars(stmt.rvalue, rvalues)
                    grab_vars(stmt.lvalue, lvalues)

                if isinstance(stmt, ir.Case):
                    valid_stmt_count = 9999999  # TODO: more elegant

                stmt_idx += 1

            if (
                (
                    rvalues.isdisjoint(lvalues) or not lvalues
                )  # make sure no rvalues depend on past lvalues
                and valid_stmt_count <= 1  # can't merge multiple _valid modifiers
                and item_idx != 0  # first item can't be merged with one before it
            ):  # can merge two case items
                # node.case_items[item_idx - 1].statements += filter(
                #     lambda stmt: not isinstance(stmt, ir.StateSubsitution),
                #     node.case_items[item_idx].statements,
                # )
                node.case_items[item_idx - 1].statements += node.case_items[
                    item_idx
                ].statements
                del node.case_items[item_idx]
            else:
                item_idx += 1
                # warnings.warn(
                #     f"cannot merge {item.to_string()} {str(lvalues)} {str(rvalues)}"
                # )
            # valid_stmt_count = 0

        # reset case-item iterations
        for idx, item in enumerate(node.case_items):
            item.condition = ir.Int(idx)

    if isinstance(node, ir.Case):
        analyze_case(node)
        # Recurse
        for item in node.case_items:
            for stmt in item.statements:
                combine_cases(stmt)
    return node
