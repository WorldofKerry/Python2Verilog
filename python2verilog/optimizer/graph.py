"""
Optimizer for the Graph IR
"""

import logging
import typing
import warnings
import random
import copy

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
    Replaces instances of variables with the mapped value
    """
    expr = copy.deepcopy(expr)
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
    try:
        node = copy.copy(node)
    except RecursionError as e:
        raise RecursionError(f"{node}") from e
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


class OptimizeGraph:
    """
    A closure for the graph optimizer
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
            mapping: dict[ir.Expression, ir.Expression],
            visited: dict[str, int],
            threshold: int,
        ):
            if regular.unique_id not in visited:
                return False
            return visited[regular.unique_id] > threshold

        def helper(
            regular: ir.Element,
            # optimal: ir.Node,
            mapping: dict[ir.Expression, ir.Expression],
            visited: dict[str, int],
            threshold: int,
        ):
            """
            Helper
            """
            if threshold <= 0 and regular.unique_id in visited:
                return regular
            visited[regular.unique_id] = visited.get(regular.unique_id, 0) + 1

            edge: ir.Edge
            if isinstance(regular, ir.Edge):
                raise RuntimeError(f"no edges allowed {regular.child}")
            if isinstance(regular, ir.AssignNode):
                new_node = graph_apply_mapping(regular, mapping)
                new_node.unique_id = f"{regular.unique_id}_{make_unique()}_optimal"

                if should_i_be_clocked(
                    regular.child.child, mapping, visited, threshold
                ):
                    new_node.optimal_child = regular.child
                    return new_node

                updated_mapping = graph_update_mapping(new_node, mapping)
                if isinstance(regular.child.child, ir.Edge):
                    raise RuntimeError(f"unexpected edge, only nodes allowed {regular}")
                result = helper(
                    regular=regular.child.child,
                    mapping=updated_mapping,
                    visited=visited,
                    threshold=threshold,
                )
                # print(f"got result {result} {result.unique_id}")
                edge = ir.NonClockedEdge(
                    unique_id=f"{regular.child.unique_id}_{make_unique()}_optimal",
                    child=result,
                )
                new_node.optimal_child = edge
                return new_node

            if isinstance(regular, ir.IfElseNode):
                new_condition = backwards_replace(regular.condition, mapping)
                new_ifelse = ir.IfElseNode(
                    unique_id=f"{regular.unique_id}_{make_unique()}_optimal",
                    condition=new_condition,
                    true_edge=regular.true_edge,
                    false_edge=regular.false_edge,
                )
                # print(
                #     f"created if with new_condition {new_condition} {new_ifelse.unique_id}"
                # )
                # print(f"created {str(ifelse)}")

                if not should_i_be_clocked(
                    regular.true_edge.child, mapping, visited, threshold
                ):
                    # print("optimzing true branch")
                    true_mapping = graph_update_mapping(regular.true_edge, mapping)
                    if isinstance(regular.true_edge.child, ir.Edge):
                        raise RuntimeError(f"{regular}")
                    optimal_true_node = helper(
                        regular=regular.true_edge.child,
                        mapping=true_mapping,
                        visited=copy.deepcopy(visited),
                        threshold=threshold,
                    )
                    edge = ir.NonClockedEdge(
                        # TODO: reason about this, there are yield -> if -> yield with no clocks in-between
                        unique_id=f"{regular.true_edge.unique_id}_{make_unique()}_optimal",
                        name="True",
                        child=optimal_true_node,
                    )
                    new_ifelse.optimal_true_edge = edge
                else:
                    # print("no optimize true branch")
                    pass

                if not should_i_be_clocked(
                    regular.false_edge.child, mapping, visited, threshold
                ):
                    # print("optimzing false branch")
                    false_mapping = graph_update_mapping(regular.false_edge, mapping)
                    if isinstance(regular.false_edge.child, ir.Edge):
                        raise RuntimeError(f"{regular}")
                    optimal_false_node = helper(
                        regular=regular.false_edge.child,
                        mapping=false_mapping,
                        visited=copy.deepcopy(visited),
                        threshold=threshold,
                    )
                    edge = ir.NonClockedEdge(
                        unique_id=f"{regular.false_edge.unique_id}_{make_unique()}_optimal",
                        name="False",
                        child=optimal_false_node,
                    )
                    new_ifelse.optimal_false_edge = edge
                else:
                    # print("No optimize false branch")
                    pass

                # print(f"returning {str(ifelse)} {mapping}")
                return new_ifelse
            if isinstance(regular, ir.YieldNode):
                updated = []
                for stmt in regular._stmts:
                    updated.append(backwards_replace(stmt, mapping))
                if isinstance(regular.child.child, ir.Edge):
                    raise RuntimeError(f"{regular}")
                # TODO: currently a clock always happens after a yield,
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
                    unique_id=f"{regular.child.unique_id}_{make_unique()}_optimal",
                    child=regular.child.child,
                )
                new_node = ir.YieldNode(
                    unique_id=f"{regular.unique_id}_{make_unique()}_optimal",
                    stmts=updated,
                    name=regular.name,
                )
                new_node.optimal_child = edge
                return new_node

            if isinstance(regular, ir.DoneNode):
                # logging.error("found done")
                return regular

            raise RuntimeError(f"unexpected {type(regular)} {regular}")

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
