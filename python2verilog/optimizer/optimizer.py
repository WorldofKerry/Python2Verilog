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


def backwards_replace(expr: ir.Expression, mapping: dict[ir.Expression, ir.Expression]):
    """
    Replaces instances of variables with the mapped value
    """
    if isinstance(expr, ir.Var):
        for key in mapping:
            if key.to_string() == expr.to_string():
                return mapping[key]
    elif isinstance(expr, ir.BinOp):
        expr.left = backwards_replace(expr.left, mapping)
        expr.right = backwards_replace(expr.right, mapping)
    elif isinstance(expr, ir.Expression):
        # TODO: add BinOp for comparison
        for key, value in mapping.items():
            expr = ir.Expression(
                expr.to_string().replace(key.to_string(), value.to_string())
            )
    return expr


def graph_apply_mapping(
    node: ir.AssignNode, mapping: dict[ir.Expression, ir.Expression]
):
    """
    Replace all rvalues of expressions in stmt with mapping
    """

    if isinstance(node, ir.AssignNode):
        # if is_dependent(node.rvalue, str(node.lvalue)):
        node.rvalue = backwards_replace(node.rvalue, mapping)
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
    unique_counter = 0

    def make_unique():
        nonlocal unique_counter
        unique_counter += 1
        return unique_counter

    def should_i_be_clocked(
        regular: ir.Node,
        # optimal: ir.Node,
        mapping: dict[ir.Expression, ir.Expression],
        visited: dict[str, int],
        threshold: int,
    ):
        if isinstance(regular, (ir.YieldNode, ir.DoneNode)):
            return True
        if regular.unique_id in visited and visited[regular.unique_id] > threshold:
            return True
        return False

    def helper(
        regular: ir.Node,
        # optimal: ir.Node,
        mapping: dict[ir.Expression, ir.Expression],
        visited: dict[str, int],
        threshold: int,
    ):
        """
        Helper
        """
        # if isinstance(regular, ir.YieldNode):
        #     print(f"return on yield")
        #     return regular
        # if regular.unique_id in visited and visited[regular.unique_id] > threshold:
        #     print(f"return on thresh")
        #     return regular
        visited[regular.unique_id] = visited.get(regular.unique_id, 1) + 1

        if isinstance(regular, ir.Edge):
            print(f"edge on {regular} {regular.child}")
            if should_i_be_clocked(
                regular, mapping, visited, threshold + 1
            ):  # + 1 accounts for pre-increment
                new_edge: ir.Edge = ir.ClockedEdge(
                    unique_id=f"{regular.unique_id}_o{make_unique()}",
                    child=regular.child,
                    name=regular.name,
                )
                return new_edge

            nextt = helper(
                regular=regular.child,
                mapping=mapping,
                visited=visited,
                threshold=threshold,
            )
            new_edge = ir.NonclockedEdge(
                unique_id=f"{regular.unique_id}_o{make_unique()}",
                child=nextt,
                name=regular.name,
            )
            return new_edge
        if isinstance(regular, ir.AssignNode):
            print(f"Took assign path")
            new_node = graph_apply_mapping(copy.deepcopy(regular), mapping)
            new_node.unique_id = f"{regular.unique_id}_o{make_unique()}"
            updated_mapping = graph_update_mapping(new_node, mapping)
            result = helper(
                regular=regular.child,
                mapping=updated_mapping,
                visited=visited,
                threshold=threshold,
            )
            new_node.child = result
            print(f"result {result.child}")
            return new_node
        if isinstance(regular, ir.IfElseNode):
            print(f"Took if path")
            true_mapping = graph_update_mapping(regular.then_edge, mapping)
            false_mapping = graph_update_mapping(regular.else_edge, mapping)
            # print(f"if {true_mapping} {false_mapping}")
            new_true_edge = helper(
                regular=regular.then_edge,
                mapping=true_mapping,
                visited=visited,
                threshold=threshold,
            )
            new_false_edge = helper(
                regular=regular.else_edge,
                mapping=false_mapping,
                visited=visited,
                threshold=threshold,
            )
            new_condition = backwards_replace(regular._condition, mapping)
            ifelse = ir.IfElseNode(
                unique_id=f"{regular.unique_id}_o{make_unique()}",
                condition=new_condition,
                true_edge=new_true_edge,
                false_edge=new_false_edge,
            )
            return ifelse
        if isinstance(regular, ir.YieldNode):
            updated = []
            for stmt in regular._stmts:
                updated.append(backwards_replace(stmt, mapping))
            regular._stmts = updated
            return ir.YieldNode(
                unique_id=f"{regular.unique_id}_o{make_unique()}",
                stmts=updated,
                edge=regular.child,
                name=regular.name,
            )
        if isinstance(regular, ir.DoneNode):
            return regular
        raise RuntimeError(f"unexpected {type(regular)} {regular}")

    if isinstance(root, ir.BasicNode):
        root.optimal_child = helper(root, {}, {}, threshold=1).child
        graph_optimize(root.child)

    return root
