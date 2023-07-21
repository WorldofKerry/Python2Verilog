"""
Optimizer algorithms that operate ontop of the intermediate representation
"""

import typing
import warnings
import random

from .. import ir


def get_idx_with_state_name(node: ir.Case, state_name: str):
    """
    Gets the index of a case item with a state name
    """
    assert isinstance(node, ir.Case)
    for idx, item in enumerate(node.case_items):
        if isinstance(item.condition, ir.Var) and item.condition.string == state_name:
            return idx
    # raise ValueError(f"Could not find state name {state_name}")
    return None


def get_last_state_sub_name(stmts: list[ir.Statement]):
    """
    Given a list of Statements, gets the state name of the last state subsitution
    """
    for stmt in reversed(stmts):
        if isinstance(stmt, ir.StateSubsitution):
            return stmt.rvalue.string
    return None


def optimize_if(root: ir.Case):
    """
    Avoids a clock cycle waste on an if statement,
    Appends the contents of the next block in the then/else blocks

    Performance: a clock cycle is saved per if-else statement cycle
    """

    def helper(node: ir.Statement):
        """
        Helper
        """
        if isinstance(node, ir.IfElse):
            then_state_name = get_last_state_sub_name(node.then_body)
            else_state_name = get_last_state_sub_name(node.else_body)

            then_state_index = get_idx_with_state_name(root, then_state_name)
            else_state_index = get_idx_with_state_name(root, else_state_name)

            if then_state_index:
                node.then_body += root.case_items[then_state_index].statements

            if else_state_index:
                node.else_body += root.case_items[else_state_index].statements

        # Recurse
        if isinstance(node, ir.Case):
            for item in node.case_items:
                for stmt in item.statements:
                    helper(stmt)

    helper(root)
    return root


def combine_cases(node: ir.Case):
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

    def one_iteration(cur_index: int, lvalues: set[str], valid_stmt_count: int = 0):
        """
        Optimizes one case item with its descendants
        """
        assert isinstance(node, ir.Case)
        # warnings.warn(f"{str([e.condition for e in node.case_items])}")
        rvalues: set[str] = set()

        for stmt in node.case_items[cur_index].statements:
            if isinstance(stmt, ir.IfElse):
                return
        check_state_name = get_last_state_sub_name(
            node.case_items[cur_index].statements
        )
        if not check_state_name:
            return
        check_state_index = get_idx_with_state_name(node, check_state_name)
        if not check_state_index:
            return
        check_state = node.case_items[check_state_index]

        for stmt in check_state.statements:
            if isinstance(stmt, ir.NonBlockingSubsitution) and not isinstance(
                stmt, ir.StateSubsitution
            ):
                grab_vars(stmt.rvalue, rvalues)
                grab_vars(stmt.lvalue, lvalues)

            if isinstance(stmt, ir.ValidSubsitution):
                valid_stmt_count += 1
                # warnings.warn(f"{str(lvalues)} {check_state.to_string()}")

            if isinstance(stmt, ir.IfElse):
                valid_stmt_count = 9999999  # TODO: more elegant

        if (
            (
                rvalues.isdisjoint(lvalues) or not lvalues
            )  # make sure no rvalues depend on past lvalues
            and valid_stmt_count <= 1  # can't merge multiple _valid modifiers
        ):
            node.case_items[cur_index].statements += node.case_items[
                check_state_index
            ].statements
            # del node.case_items[check_state_index] # Breaks circle lines
            one_iteration(cur_index, lvalues, valid_stmt_count)

    assert isinstance(node, ir.Case)
    cur_index = 0
    while cur_index < len(node.case_items):
        lvalues: set[str] = set()
        valid_stmt_count = 0

        for stmt in node.case_items[cur_index].statements:
            if isinstance(stmt, ir.NonBlockingSubsitution) and not isinstance(
                stmt, ir.StateSubsitution
            ):
                grab_vars(stmt.lvalue, lvalues)

            if isinstance(stmt, ir.ValidSubsitution):
                valid_stmt_count += 1

            if isinstance(stmt, ir.IfElse):
                valid_stmt_count = 9999999  # TODO: more elegant

        one_iteration(cur_index, lvalues, valid_stmt_count)
        cur_index += 1
    # one_iteration(0, set())

    return node
