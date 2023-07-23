"""
Optimizer algorithms that operate ontop of the intermediate representation
"""

import typing
import warnings
import random
import copy

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


def combine_cases(root: ir.Case):
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
        assert isinstance(root, ir.Case)
        # warnings.warn(f"{str([e.condition for e in node.case_items])}")
        rvalues: set[str] = set()

        for stmt in root.case_items[cur_index].statements:
            if isinstance(stmt, ir.IfElse):
                return
        check_state_name = get_last_state_sub_name(
            root.case_items[cur_index].statements
        )
        if not check_state_name:
            return
        check_state_index = get_idx_with_state_name(root, check_state_name)
        if not check_state_index:
            return
        check_state = root.case_items[check_state_index]

        for stmt in check_state.statements:
            if isinstance(stmt, ir.NonBlockingSubsitution):
                grab_vars(stmt.rvalue, rvalues)
                grab_vars(stmt.lvalue, lvalues)

            if isinstance(stmt, ir.ValidSubsitution):
                valid_stmt_count += 1

            if isinstance(stmt, ir.IfElse):
                valid_stmt_count = 9999999  # TODO: more elegant

        if (
            rvalues.isdisjoint(lvalues) or not lvalues
        ) and valid_stmt_count <= 1:  # can't merge multiple _valid modifiers
            root.case_items[cur_index].statements += root.case_items[
                check_state_index
            ].statements
            one_iteration(cur_index, lvalues, valid_stmt_count)

    assert isinstance(root, ir.Case)
    cur_index = 0
    while cur_index < len(root.case_items):
        lvalues: set[str] = set()
        valid_stmt_count = 0

        for stmt in root.case_items[cur_index].statements:
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

    return root


def remove_unreferenced_states(root: ir.Case):
    """
    Removes unreferenced states,
    that is states that are not accessible by the state machine

    Note: does not affect performance
    """

    def cleanup_unused_items(node: ir.Case):
        """
        Reference counts every case expression and removes a case if no one references it
        """
        referenced: set[str] = set()

        def helper(node: ir.Statement):
            """
            Helper
            """
            if isinstance(node, ir.StateSubsitution):
                referenced.add(node.rvalue.string)
            if isinstance(node, ir.IfElse):
                for stmt in node.then_body:
                    helper(stmt)
                for stmt in node.else_body:
                    helper(stmt)

        for i, item in enumerate(node.case_items):
            if i == 0:
                continue  # first case-item is entry
            for stmt in item.statements:
                helper(stmt)

        all_states: set[str] = set()
        for i, item in enumerate(node.case_items):
            if i == 0:
                continue
            all_states.add(item.condition.string)

        diff = all_states - referenced
        for i, item in enumerate(node.case_items):
            if i == 0:
                continue
            if item.condition.string in diff:
                del node.case_items[i]

        # warnings.warn(
        #     f"{str(referenced)} {str(all_states)} {str(all_states - referenced)}"
        # )

    def remove_redundant_state_changes(node: ir.Case):
        """
        If there multiple state assignments, only last one is used
        Therefore the earlier ones should be removed
        """

        def filterer(stmts: list[ir.Statement]):
            """
            Helper
            """
            stmts.reverse()
            saw_state_sub = False
            result: list[ir.Statement] = []
            for stmt in stmts:
                if isinstance(stmt, ir.StateSubsitution):
                    if not saw_state_sub:
                        result.append(stmt)
                        saw_state_sub = True
                else:
                    result.append(stmt)
            result.reverse()
            return result

        def helper(node: ir.Statement):
            """
            Helper
            """
            if isinstance(node, ir.IfElse):
                node.then_body = filterer(node.then_body)
                node.else_body = filterer(node.else_body)

        for item in node.case_items:
            item.statements = filterer(item.statements)
            for stmt in item.statements:
                helper(stmt)

    remove_redundant_state_changes(root)
    cleanup_unused_items(root)

    return root


def do_item(root: ir.Case, state_name: str):
    """
    Optimizes an item
    """
    state_idx = get_idx_with_state_name(root, state_name)
    state = root.case_items[state_idx]
    state.statements = do_stmts(root, state.statements, {}, False, {state_name})


def do_backwards_replace(
    stmt: ir.Statement, mapping: dict[ir.Expression, ir.Expression]
):
    """
    Replace all rvalues of expressions in stmt with mapping
    """

    def helper(expr: ir.Expression):
        if isinstance(expr, ir.Var):
            warnings.warn(f"doing var {expr} {mapping}")
            for key in mapping:
                warnings.warn(f"iterating {key.to_string()} {expr.to_string()}")
                if key.to_string() == expr.to_string():
                    warnings.warn(
                        f"success {key.to_string()} replaced with {mapping[key]}"
                    )
                    return mapping[key]
        if isinstance(expr, ir.BinOp):
            # warnings.warn(f"found binop {expr} {mapping}")
            # warnings.warn(f"wtf {helper(expr.left)}")
            expr.left = helper(expr.left)
            # expr.left = ir.Expression("fk me sideways")
            # expr.left = None
            # warnings.warn(f"binop left {expr} {mapping}")
            expr.right = helper(expr.right)
            # warnings.warn(f"done binop {expr} {mapping}")
        return expr

    if isinstance(stmt, ir.NonBlockingSubsitution):
        warnings.warn(f"checking {stmt} {mapping}")
        stmt.rvalue = helper(stmt.rvalue)
    else:
        raise ValueError(f"Cannot do backwards replace on {stmt}")


def do_stmts(
    root: ir.Case,
    stmts: list[ir.Statement],
    mapping: dict[ir.Expression, ir.Expression],
    yielded: bool,
    visited: set[str],
):
    """
    Optimizes a list of statements
    """
    og_stmts = copy.deepcopy(stmts)
    for stmt in stmts:
        if isinstance(stmt, ir.ValidSubsitution):
            if yielded:
                return og_stmts
            yielded = True
        if isinstance(stmt, ir.NonBlockingSubsitution):
            # warnings.warn(f"backward replace {stmt} {mapping}")
            do_backwards_replace(stmt, mapping)
            # warnings.warn(f"backward done {stmt} {mapping}")
        elif isinstance(stmt, ir.IfElse):
            then_mapping = copy.deepcopy(mapping)
            else_mapping = copy.deepcopy(mapping)
            stmt.then_body = do_stmts(
                root, stmt.then_body, then_mapping, yielded, visited
            )
            stmt.else_body = do_stmts(
                root, stmt.else_body, else_mapping, yielded, visited
            )
            return stmts
        else:
            raise ValueError(f"Cannot optimize {stmt}")
    new_mapping = {}
    for stmt in stmts:
        assert not isinstance(stmt, ir.IfElse), "Should have been handled"
        if isinstance(stmt, ir.NonBlockingSubsitution):
            new_mapping[stmt.lvalue] = stmt.rvalue
    next_state = get_last_state_sub_name(stmts)
    next_state_idx = get_idx_with_state_name(root, next_state)
    if next_state_idx:
        state = root.case_items[get_idx_with_state_name(root, next_state)]
        visited.add(next_state)
        return stmts + do_stmts(root, state.statements, new_mapping, yielded, visited)
    return stmts
