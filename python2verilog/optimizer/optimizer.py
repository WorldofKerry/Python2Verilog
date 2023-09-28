"""
Optimizer for the Graph IR
"""

import copy
import logging
import typing
from functools import reduce

from python2verilog.utils.assertions import get_typed

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
        logging.debug(f"TODO: use the State class {expr.to_string()}")
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
        self.unique_counter = 0  # warning due to recursion can't be static var of func

    def make_unique(self):
        """
        Makes a unique value
        """
        self.unique_counter += 1
        return self.unique_counter

    @staticmethod
    def should_i_be_clocked(
        node: ir.Element,
        visited: dict[str, int],
        threshold: int,
    ):
        """
        Returns true if edge should be clocked,
        that is visited this node more than threshold times
        """
        be_clocked = False
        if node.unique_id in visited and visited[node.unique_id] > threshold:
            be_clocked = True
        if (
            isinstance(node, ir.AssignNode)
            and isinstance(node.lvalue, ir.ExclusiveVar)
            and node.lvalue.ver_name in visited
        ):
            be_clocked = True
        return be_clocked

    @staticmethod
    def helper(
        element: ir.Node,
        mapping: dict[ir.Expression, ir.Expression],
        visited: dict[str, int],
        threshold: int,
    ):
        """
        Recursive helper
        """
        return element

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

        if root.unique_id in visited:
            return
        logging.debug(f"optimizing {root.unique_id} {root}")
        visited.add(root.unique_id)
        if isinstance(root, ir.BasicElement) and isinstance(root, ir.Node):
            root.optimal_child = self.helper(
                root, {}, {}, threshold=threshold
            ).optimal_child
            self.__graph_optimize(root.child.child, visited, threshold=threshold)
        elif isinstance(root, ir.IfElseNode):
            root.optimal_true_edge = self.helper(
                root, {}, {}, threshold=threshold
            ).optimal_true_edge
            root.optimal_false_edge = self.helper(
                root, {}, {}, threshold=threshold
            ).optimal_false_edge
            self.__graph_optimize(root.true_edge.child, visited, threshold=threshold)
            self.__graph_optimize(root.false_edge.child, visited, threshold=threshold)
        elif isinstance(root, ir.DoneNode):
            pass
        else:
            raise RuntimeError(f"{type(root)}")
