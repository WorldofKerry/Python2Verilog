"""
Optimizer for the Graph IR
"""

import copy
import logging
import typing

from .. import ir


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
    If the expression matches a key in the mapping, it is replaced with
    the corresponding value in the mapping.

    :return: a copy of the updated expression.
    """
    expr = copy.deepcopy(expr)
    if isinstance(expr, ir.Var):
        for key in mapping:
            if key.to_string() == expr.to_string():
                return mapping[key]
    elif isinstance(expr, (ir.UInt, ir.Int)):
        return expr
    elif isinstance(expr, (ir.BinOp, ir.UBinOp)):
        expr.left = backwards_replace(expr.left, mapping)
        expr.right = backwards_replace(expr.right, mapping)
    elif isinstance(expr, ir.Ternary):
        expr.condition = backwards_replace(expr.condition, mapping)
        expr.left = backwards_replace(expr.left, mapping)
        expr.right = backwards_replace(expr.right, mapping)
    elif isinstance(expr, ir.UnaryOp):
        expr.expr = backwards_replace(expr.expr, mapping)
    else:
        logging.debug(f"TODO: use the State class {type(expr)} {expr}")
    return expr


def graph_apply_mapping(
    node: ir.AssignNode, mapping: dict[ir.Expression, ir.Expression]
):
    """
    If the right-hand-side of an assignment (e.g. the `b` in `a = b`)
    matches a key in the mapping, it will be replaced with the
    corresponding value in the mapping.

    :return: a node with the mapping applied
    """
    try:
        node = copy.copy(node)
    except RecursionError as e:
        raise RecursionError(f"{node}") from e
    if isinstance(node, ir.AssignNode):
        node.rvalue = backwards_replace(node.rvalue, mapping)
    else:
        raise ValueError(f"Cannot do backwards replace on {node}")
    return node


def graph_update_mapping(
    stmt: ir.Element, old_mapping: dict[ir.Expression, ir.Expression]
):
    """
    Updates mapping with statements' contents
    """
    new_mapping = copy.deepcopy(old_mapping)
    assert not isinstance(
        stmt, ir.IfElseNode
    ), "Should have been handled, call this method twice on the two branches"
    if isinstance(stmt, ir.AssignNode):
        new_mapping[stmt.lvalue] = stmt.rvalue
    return new_mapping


class OptimizeGraph:
    """
    A closure for the graph optimizer

    `threshold` (an integer >= 0) tunes
    how much an algorithm can be unrolled and duplicated

    A larger `threshold` will result in a reduction in clock cycles,
    but an increase in hardware usage

    If a python generator function generates all of its outputs in O(n) time:

        1) hardware optimized with `threshold=0` completes in O(n) cycles

        2) hardware optimized with `threshold=x` for `x > 0` completes in O(n/(x+1)) cycles

    """

    def __init__(self, root: ir.Element, threshold: int = 0):
        self.__graph_optimize(root, threshold=threshold)

    unique_counter = 0  # warning due to recursion can't be static var of func

    def __graph_optimize(
        self,
        root: ir.Element,
        visited: typing.Optional[set[str]] = None,
        threshold: int = 0,
    ):
        """
        Optimizes a single node, creating branches
        Returns the improved root node
        """
        if visited is None:
            visited = set()

        def make_unique():
            self.unique_counter += 1
            return self.unique_counter

        def should_i_be_clocked(
            regular: ir.Element,
            visited: dict[str, int],
            threshold: int,
        ):
            if regular.unique_id not in visited:
                return False
            return visited[regular.unique_id] > threshold

        def helper(
            element: ir.Element,
            mapping: dict[ir.Expression, ir.Expression],
            visited: dict[str, int],
            threshold: int,
        ):
            """
            Helper
            """
            if threshold <= 0 and element.unique_id in visited:
                return element
            visited[element.unique_id] = visited.get(element.unique_id, 0) + 1

            edge: ir.Edge
            if isinstance(element, ir.Edge):
                raise RuntimeError(f"no edges allowed {element.child}")
            if isinstance(element, ir.AssignNode):
                new_node = graph_apply_mapping(element, mapping)
                new_node.unique_id = f"{element.unique_id}_{make_unique()}_optimal"

                if should_i_be_clocked(element.child.child, visited, threshold):
                    new_node.optimal_child = element.child
                    return new_node

                updated_mapping = graph_update_mapping(new_node, mapping)
                if isinstance(element.child.child, ir.Edge):
                    raise RuntimeError(f"unexpected edge, only nodes allowed {element}")
                result = helper(
                    element=element.child.child,
                    mapping=updated_mapping,
                    visited=visited,
                    threshold=threshold,
                )
                # print(f"got result {result} {result.unique_id}")
                edge = ir.NonClockedEdge(
                    unique_id=f"{element.child.unique_id}_{make_unique()}_optimal",
                    child=result,
                )
                new_node.optimal_child = edge
                return new_node

            if isinstance(element, ir.IfElseNode):
                new_condition = backwards_replace(element.condition, mapping)
                new_node = ir.IfElseNode(
                    unique_id=f"{element.unique_id}_{make_unique()}_optimal",
                    condition=new_condition,
                    true_edge=element.true_edge,
                    false_edge=element.false_edge,
                )
                # print(
                #     f"created if with new_condition {new_condition} {new_ifelse.unique_id}"
                # )
                # print(f"created {str(ifelse)}")

                if not should_i_be_clocked(element.true_edge.child, visited, threshold):
                    # print("optimzing true branch")
                    true_mapping = graph_update_mapping(element.true_edge, mapping)
                    if isinstance(element.true_edge.child, ir.Edge):
                        raise RuntimeError(f"{element}")
                    optimal_true_node = helper(
                        element=element.true_edge.child,
                        mapping=true_mapping,
                        visited=copy.deepcopy(visited),
                        threshold=threshold,
                    )
                    edge = ir.NonClockedEdge(
                        # There may be yield -> if -> yield with no clocks in-between
                        unique_id=f"{element.true_edge.unique_id}_{make_unique()}_optimal",
                        name="True",
                        child=optimal_true_node,
                    )
                    new_node.optimal_true_edge = edge
                else:
                    # print("no optimize true branch")
                    pass

                if element.false_edge:
                    if not should_i_be_clocked(
                        element.false_edge.child, visited, threshold
                    ):
                        # print("optimzing false branch")
                        false_mapping = graph_update_mapping(
                            element.false_edge, mapping
                        )
                        if isinstance(element.false_edge.child, ir.Edge):
                            raise RuntimeError(f"{element}")
                        optimal_false_node = helper(
                            element=element.false_edge.child,
                            mapping=false_mapping,
                            visited=copy.deepcopy(visited),
                            threshold=threshold,
                        )
                        edge = ir.NonClockedEdge(
                            unique_id=f"{element.false_edge.unique_id}_{make_unique()}_optimal",
                            name="False",
                            child=optimal_false_node,
                        )
                        new_node.optimal_false_edge = edge
                    else:
                        # print("No optimize false branch")
                        pass

                # print(f"returning {str(ifelse)} {mapping}")
                return new_node
            if isinstance(element, ir.YieldNode):
                updated = []
                for stmt in element.stmts:
                    updated.append(backwards_replace(stmt, mapping))
                if isinstance(element.child.child, ir.Edge):
                    raise RuntimeError(f"{element}")
                # Currently a clock always happens after a yield,
                # this results in inefficiencies when there is a yield followed by done
                # more wave analysis can be done to potentially paramatize this
                # e.g. can valid and done both be 1 in the same clock cycle?

                # result = helper(
                #     regular=regular.child.child,
                #     mapping=mapping,
                #     visited=visited,
                #     threshold=threshold,
                # )
                # edge = ir.NonClockedEdge(
                #     unique_id=f"{regular.child.unique_id}_{make_unique()}_optimal",
                #     child=result,
                # )

                edge = ir.ClockedEdge(
                    unique_id=f"{element.child.unique_id}_{make_unique()}_optimal",
                    child=element.child.child,
                )
                new_node = ir.YieldNode(
                    unique_id=f"{element.unique_id}_{make_unique()}_optimal",
                    stmts=updated,
                    name=element.name,
                )
                new_node.optimal_child = edge
                return new_node

            if isinstance(element, ir.DoneNode):
                # logging.error("found done")
                # print("found done node")
                return element

            raise RuntimeError(f"unexpected {type(element)} {element}")

        if root.unique_id in visited:
            return root
        # print(f"==> optimizing {str(root)}")
        visited.add(root.unique_id)
        if isinstance(root, ir.BasicElement):
            root.optimal_child = helper(root, {}, {}, threshold=threshold).optimal_child
            self.__graph_optimize(root.child.child, visited, threshold=threshold)
        elif isinstance(root, ir.IfElseNode):
            root.optimal_true_edge = helper(
                root, {}, {}, threshold=threshold
            ).optimal_true_edge
            root.optimal_false_edge = helper(
                root, {}, {}, threshold=threshold
            ).optimal_false_edge
            self.__graph_optimize(root.true_edge.child, visited, threshold=threshold)
            self.__graph_optimize(root.false_edge.child, visited, threshold=threshold)
        elif isinstance(root, ir.DoneNode):
            pass
        elif isinstance(root, ir.Edge):
            raise RuntimeError()
        else:
            raise RuntimeError(f"{type(root)}")
