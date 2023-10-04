"""
Optimizer for the Graph IR
"""

import copy
import logging
from functools import reduce
from typing import Any, Callable, Iterator, Optional, Union

from python2verilog.utils.typed import guard, typed

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


def backwards_replace(expr: ir.Expression, mapping: dict[ir.Var, ir.Expression]):
    """
    If the expression matches a key in the mapping, it is replaced with
    the corresponding value in the mapping.

    Note: ignores exclusive vars in replacement process

    :return: a copy of the updated expression.
    """
    expr = copy.deepcopy(expr)
    if isinstance(expr, ir.Var):
        if not isinstance(expr, ir.ExclusiveVar):
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
        raise TypeError(f"{type(expr)} {expr}")
    return expr


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

    def __init__(self, root: ir.Node, threshold: int = 0):
        self.unique_counter = 0  # warning due to recursion can't be static var of func
        self.reduce_cycles(root, threshold=threshold)

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
    def update_visited(node: ir.Node, visited: dict[str, int]):
        """
        Updates visited
        """

    @staticmethod
    def exclusive_vars(variables) -> Iterator[ir.ExclusiveVar]:
        """
        Filters for exclusive variables
        """
        return filter(lambda var: isinstance(var, ir.ExclusiveVar), variables)

    @staticmethod
    def map_to_ver_name(variables) -> Iterator[str]:
        """
        Maps a variable to its ver_name
        """
        return map(lambda var: var.ver_name, variables)

    @staticmethod
    def chain_generators(
        iterable: Iterator[Any], *functions: Callable[[Iterator[Any]], Iterator[Any]]
    ) -> Iterator[Any]:
        """
        Applies transformations to iterators
        """
        for func in functions:
            iterable = func(iterable)
        yield from iterable

    # Eventually yield nodes should be removed and be replaced with exclusive vars
    YIELD_VISITOR_ID = "__YIELD_VISITOR_ID"

    def reduce_cycles_visit(
        self,
        edge: ir.Edge,
        mapping: dict[ir.Var, ir.Expression],
        visited: dict[Union[str, ir.Var], int],
        threshold: int,
    ) -> ir.Edge:
        """
        Recursively visits the children, conditionally adding them to an optimal path

        The concept of mapping is as follows:

        If
        a = 1
        b = a
        then b == 1, if no clock cycle occurs in-between,
        at the end of this block, mapping would be
        {a: 1, b: 1}

        :param mapping: values of variables, given the previous logic
        :param visited: visited unique_ids and exclusive vars
        """
        node = edge.child
        assert node

        logging.debug(
            "%s %s %s", self.reduce_cycles_visit.__name__, edge.child, mapping
        )

        # Check for cyclic paths
        if (
            isinstance(edge, ir.ClockedEdge)
            and node.unique_id in visited
            and visited[node.unique_id] > threshold
        ):
            return edge

        # Exclusive vars can only be visited once
        exclusive_vars = set(self.exclusive_vars(node.variables()))
        if exclusive_vars & visited.keys():
            logging.debug(
                f"Already visited {exclusive_vars & visited.keys()}"
                ", ending current optimization"
                f" {exclusive_vars} {visited.keys()}"
            )
            if isinstance(edge, ir.ClockedEdge):
                return edge
            return ir.ClockedEdge(
                unique_id=f"{edge.unique_id}_{self.make_unique()}_optimal", child=node
            )

        # Update visited
        if isinstance(node, ir.AssignNode) and isinstance(node.lvalue, ir.ExclusiveVar):
            visited[node.lvalue] = 1
        visited[node.unique_id] = visited.get(node.unique_id, 0) + 1

        new_edge: ir.Edge = ir.NonClockedEdge(
            unique_id=f"{edge.unique_id}_{self.make_unique()}_optimal"
        )
        if isinstance(node, ir.IfElseNode):
            new_edge.child = ir.IfElseNode(
                unique_id=f"{node.unique_id}_{self.make_unique()}_optimal",
                condition=backwards_replace(node.condition, mapping),
                true_edge=self.reduce_cycles_visit(
                    edge=node.true_edge,
                    mapping=copy.deepcopy(mapping),
                    visited=copy.deepcopy(visited),
                    threshold=threshold,
                ),
                false_edge=self.reduce_cycles_visit(
                    edge=node.false_edge,
                    mapping=copy.deepcopy(mapping),
                    visited=copy.deepcopy(visited),
                    threshold=threshold,
                ),
            )
        elif isinstance(node, ir.AssignNode):
            new_rvalue = backwards_replace(node.rvalue, mapping)
            mapping[node.lvalue] = new_rvalue
            assert guard(node.child, ir.Edge)
            new_edge.child = ir.AssignNode(
                unique_id=f"{node.unique_id}_{self.make_unique()}_optimal",
                lvalue=node.lvalue,
                rvalue=new_rvalue,
                child=self.reduce_cycles_visit(
                    edge=node.child,
                    mapping=mapping,
                    visited=visited,
                    threshold=threshold,
                ),
            )
        elif isinstance(node, ir.YieldNode):
            # Yield node can only be visited once
            assert guard(node.child, ir.Edge)
            if self.YIELD_VISITOR_ID in visited:
                new_edge.child = self.reduce_cycles_visit(
                    edge=node.child,
                    mapping=mapping,
                    visited=visited,
                    threshold=threshold,
                )
                visited[self.YIELD_VISITOR_ID] = 1
            else:
                new_edge = ir.ClockedEdge(
                    unique_id=f"{edge.unique_id}_{self.make_unique()}_optimal",
                    child=node,
                )
        elif isinstance(node, ir.DoneNode):
            new_edge.child = node
        else:
            raise RuntimeError(f"{type(node)}")
        return new_edge

    def reduce_cycles(
        self,
        root: ir.Node,
        visited: Optional[set[str]] = None,
        threshold: int = 0,
    ) -> None:
        """
        Optimizes a node, by increasing amount of work done in a cycle
        by adding nonclocked edges
        """
        if visited is None:
            visited = set()
        if root.unique_id in visited:
            return
        visited.add(root.unique_id)

        if isinstance(root, ir.BasicElement) and isinstance(root, ir.Node):
            # This ifelse should be looked at
            mapper: dict[ir.Var, ir.Expression]
            if isinstance(root, ir.AssignNode):
                mapper = {root.lvalue: root.rvalue}
            else:
                mapper = {}

            assert guard(root.child, ir.Edge)
            assert guard(root.child.child, ir.Node)
            root.optimal_child = self.reduce_cycles_visit(
                root.child, mapper, {}, threshold=threshold
            )
            self.reduce_cycles(root.child.child, visited, threshold=threshold)
        elif isinstance(root, ir.IfElseNode):
            root.optimal_true_edge = self.reduce_cycles_visit(
                root.true_edge, {}, {}, threshold=threshold
            )
            root.optimal_false_edge = self.reduce_cycles_visit(
                root.false_edge, {}, {}, threshold=threshold
            )
            self.reduce_cycles(root.true_edge.child, visited, threshold=threshold)
            self.reduce_cycles(root.false_edge.child, visited, threshold=threshold)
        elif isinstance(root, ir.DoneNode):
            pass
        else:
            raise RuntimeError(f"{type(root)}")
        logging.debug("%s => %s", root, list(root.nonclocked_children()))
