"""
IncreaseWorkPerClockCycle
"""

import copy
import logging
from functools import reduce
from typing import Any, Callable, Iterator, Optional, Union

from python2verilog import ir
from python2verilog.optimizer.helpers import backwards_replace
from python2verilog.utils.typed import guard, typed


class IncreaseWorkPerClockCycle:
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
        self.perma_visited: set[str] = set()
        self.apply(root, threshold=threshold)

    def make_unique(self):
        """
        Makes a unique value
        """
        self.unique_counter += 1
        return self.unique_counter

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

    def apply_recursive(
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
        logging.debug("%s on %s", self.apply_recursive.__name__, node)

        # Check for cyclic paths
        if node.unique_id in visited and visited[node.unique_id] > threshold:
            if isinstance(edge, ir.NonClockedEdge):
                # A bit suspicious
                logging.debug("pretty sus %s", node)
            # self.apply(node, threshold=threshold)
            return edge

        # Exclusive vars can only be visited once
        exclusive_vars = set(self.exclusive_vars(node.variables()))
        if exclusive_vars & visited.keys():
            logging.debug(
                "Intersection %s = {%s & %s} ending on %s",
                exclusive_vars & visited.keys(),
                exclusive_vars,
                visited.keys(),
                node,
            )
            if isinstance(edge, ir.ClockedEdge):
                return edge
            else:
                self.apply(node, threshold=threshold)
                return ir.ClockedEdge(
                    unique_id=f"{edge.unique_id}_{self.make_unique()}_optimal",
                    child=node,
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
                true_edge=self.apply_recursive(
                    edge=node.true_edge,
                    mapping=copy.deepcopy(mapping),
                    visited=copy.deepcopy(visited),
                    threshold=threshold,
                ),
                false_edge=self.apply_recursive(
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
                child=self.apply_recursive(
                    edge=node.child,
                    mapping=mapping,
                    visited=visited,
                    threshold=threshold,
                ),
            )
        elif isinstance(node, ir.DoneNode):
            new_edge.child = node
        else:
            raise RuntimeError(f"{type(node)}")
        return new_edge

    def apply(
        self,
        root: ir.Node,
        threshold: int = 0,
    ) -> None:
        """
        Optimizes a node, by increasing amount of work done in a cycle
        by adding nonclocked edges
        """
        logging.info("%s on %s", self.apply.__name__, root)

        if root.unique_id in self.perma_visited:
            return
        self.perma_visited.add(root.unique_id)

        if isinstance(root, ir.BasicElement) and isinstance(root, ir.Node):
            # Could be cleaned up
            mapper: dict[ir.Var, ir.Expression]
            visitedd: dict[Union[ir.Var, str], int]
            lvalue: ir.Var
            match root:
                case ir.AssignNode(lvalue=lvalue, rvalue=rvalue) if isinstance(
                    lvalue, ir.ExclusiveVar
                ):
                    mapper = {lvalue: rvalue}
                    visitedd = {lvalue: 1}
                case ir.AssignNode(lvalue=lvalue, rvalue=rvalue):
                    mapper = {lvalue: rvalue}
                    visitedd = {}
                case _:
                    mapper = {}
                    visitedd = {}

            assert guard(root.child, ir.Edge)
            assert guard(root.child.child, ir.Node)
            root.optimal_child = self.apply_recursive(
                root.child, mapper, visitedd, threshold=threshold
            )
            # if isinstance(root.child, ir.ClockedEdge):
            #     self.reduce_cycles(root.child.child, threshold=threshold)
            self.apply(root.child.child, threshold=threshold)
        elif isinstance(root, ir.IfElseNode):
            root.optimal_true_edge = self.apply_recursive(
                root.true_edge, {}, {}, threshold=threshold
            )
            root.optimal_false_edge = self.apply_recursive(
                root.false_edge, {}, {}, threshold=threshold
            )
            # if isinstance(root.true_edge, ir.ClockedEdge):
            #     self.reduce_cycles(root.true_edge.child, threshold=threshold)
            # if isinstance(root.false_edge, ir.ClockedEdge):
            #     self.reduce_cycles(root.false_edge.child, threshold=threshold)
            self.apply(root.true_edge.child, threshold=threshold)
            self.apply(root.false_edge.child, threshold=threshold)
        elif isinstance(root, ir.DoneNode):
            pass
        else:
            raise RuntimeError(f"{type(root)}")
        logging.debug("Optimized to %s => %s", root, list(root.nonclocked_children()))
