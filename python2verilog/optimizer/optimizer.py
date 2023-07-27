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
            grab_vars(expr._left, variables)
            grab_vars(expr._right, variables)

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


def is_dependent(expr: ir.Expression, var: str):
    """
    Returns whether or not expr is dependent on var
    """
    if isinstance(expr, ir.Var):
        return var == expr.to_string()
    if isinstance(expr, ir.BinOp):
        return is_dependent(expr.left, var) or is_dependent(expr.right, var)
    if isinstance(expr, ir.Int):
        return False
    raise TypeError(f"unexpected {type(expr)}")


def graph_apply_mapping(
    node: ir.AssignNode, mapping: dict[ir.Expression, ir.Expression]
):
    """
    Replace all rvalues of expressions in stmt with mapping
    """

    def dependent_helper(expr: ir.Expression):
        """
        i <= f(i), e.g. i <= i + 1
        """
        # print(f"recurse {type(expr)} {expr}")
        if isinstance(expr, ir.Var):
            # print(f"found var {expr}")
            for key in mapping:
                if key.to_string() == expr.to_string():
                    # print(f"found {mapping[key]}")
                    return mapping[key]
        if isinstance(expr, ir.BinOp):
            expr.left = dependent_helper(expr.left)
            expr.right = dependent_helper(expr.right)
        return expr

    def independent_helper(lvalue: str, rvalue: ir.Expression):
        """
        i <= constant, e.g. i <= 0
        """

        def helper(expr: ir.Expression, replacement: ir.Expression):
            if isinstance(expr, ir.BinOp):
                if expr.left.to_string() == lvalue:
                    expr.left = copy.deepcopy(replacement)
                if expr.right.to_string() == lvalue:
                    expr.right = copy.deepcopy(replacement)
                helper(expr.left, replacement)
                helper(expr.right, replacement)
            return expr

        print("independent")
        for key in mapping:
            if key.to_string() == lvalue:
                return helper(mapping[key], rvalue)
        warnings.warn("Untested branch")  # temp comment out
        return rvalue

    if isinstance(node, ir.AssignNode):
        if is_dependent(node.rvalue, str(node.lvalue)):
            node.rvalue = dependent_helper(node.rvalue)
        else:
            print(f"{node.lvalue} {node.rvalue}")
            node.rvalue = independent_helper(str(node.lvalue), node.rvalue)
    else:
        raise ValueError(f"Cannot do backwards replace on {node}")
    return node


def graph_update_mapping(
    stmt: ir.Statement, old_mapping: dict[ir.Expression, ir.Expression]
):
    """
    Updates mapping with statements' contents
    """
    new_mapping = copy.deepcopy(old_mapping)
    assert not isinstance(
        stmt, ir.IfElse
    ), "Should have been handled, call this method twice on the two branches"
    if isinstance(stmt, ir.AssignNode):
        new_mapping[stmt.lvalue] = stmt.rvalue
    return new_mapping


def graph_optimize(root: ir.Node):
    """
    Optimizes a single node, creating branches
    Returns the improved root node
    """

    def helper(
        node: ir.Node,
        mapping: dict[ir.Expression, ir.Expression],
        visited: dict[str, int],
        threshold: int,
    ):
        """
        Helper
        """
        if node.unique_id in visited and visited[node.unique_id] > threshold:
            return node
        visited[node.unique_id] = visited.get(node.unique_id, 0) + 1

        if isinstance(node, ir.Edge):
            result = helper(
                node=node.child, mapping=mapping, visited=visited, threshold=threshold
            )
        if isinstance(node, ir.AssignNode):
            print(f"assign before {mapping} {node} {type(node.rvalue)}")
            updated_node = graph_apply_mapping(copy.deepcopy(node), mapping)
            mapping = graph_update_mapping(updated_node, mapping)
            print(f"assign after {mapping} {updated_node}")
            print(f"updated {updated_node}")
            result = helper(
                node=updated_node.child,
                mapping=mapping,
                visited=visited,
                threshold=threshold,
            )
            edge = ir.NonclockedEdge(unique_id=node.child.unique_id)
        if isinstance(node, ir.IfElseNode):
            true_mapping = graph_update_mapping(node.children[0], mapping)
            false_mapping = graph_update_mapping(node.children[1], mapping)
            print(f"if {true_mapping} {false_mapping}")
            helper(
                node=node.then_edge,
                mapping=mapping,
                visited=visited,
                threshold=threshold,
            )
            helper(
                node=node.else_edge,
                mapping=mapping,
                visited=visited,
                threshold=threshold,
            )
        return node

    root = helper(root, {}, {}, threshold=2)

    return root
