"""
IncreaseWorkPerClockCycle
"""

import copy
import itertools
import logging
from typing import Any, Callable, Iterator, Union

from python2verilog import ir
from python2verilog.optimizer.helpers import backwards_replace
from python2verilog.utils.peek_counter import PeekCounter
from python2verilog.utils.typed import guard, guard_dict, typed


class IncreaseWorkPerClockCycle:
    """
    A closure for the increase work per clock cycle optimizer

    `threshold` (an integer >= 0) tunes
    how much the code can be unrolled (and duplicated)

    A larger `threshold` will result in a reduction in clock cycles,
    but an increase in hardware usage

    If a python generator function generates all of its outputs in O(n) time:

        1) hardware optimized with `threshold=0` completes in O(n) cycles

        2) hardware optimized with `threshold=x` for `x > 0` completes in O(n/(x+1)) cycles
    """

    def __init__(self, root: ir.Node, threshold: int = 0):
        self.visited: set[str] = set()
        self.threshold = threshold

        counter = PeekCounter()
        self.make_unique = counter.next
        self.make_unique_peek = counter.peek

        self.apply(root)

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
        new_mapping: dict[ir.Var, ir.Expression],
        old_mapping: dict[ir.Var, ir.Expression],
        visited_path: dict[Union[str, ir.Var], int],
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
        :param visited: visited unique_ids and exclusive vars for this nonclocked sequence
        """
        assert guard(edge, ir.Edge)
        assert guard_dict(new_mapping, ir.Var, ir.Expression)
        assert guard_dict(old_mapping, ir.Var, ir.Expression)
        assert guard(visited_path, dict)
        for key, value in visited_path.items():
            assert isinstance(key, (str, ir.Var))
            assert guard(value, int)

        node = edge.child
        assert node
        logging.debug(
            "%s node %s, new %s, old %s",
            self.apply_recursive.__name__,
            node,
            new_mapping,
            old_mapping,
        )

        # if self.make_unique_peek() == 10:
        #     breakpoint()

        # If clocked, then switch to new mapping
        if isinstance(edge, ir.ClockedEdge):
            old_mapping = copy.copy(new_mapping)

        # Check for cyclic paths
        if (
            node.unique_id in visited_path
            and visited_path[node.unique_id] > self.threshold
        ):
            assert guard(node, ir.Node)
            self.apply(node)
            return edge

        # Exclusive vars can only be visited once
        exclusive_vars = set(self.exclusive_vars(node.variables()))
        if exclusive_vars & visited_path.keys():
            logging.debug(
                "Intersection %s = {%s & %s} ending on %s",
                exclusive_vars & visited_path.keys(),
                exclusive_vars,
                visited_path.keys(),
                node,
            )
            if isinstance(edge, ir.ClockedEdge):
                assert guard(node, ir.Node)
                self.apply(node)
            return edge

        # Update visited
        if isinstance(node, ir.AssignNode) and isinstance(node.lvalue, ir.ExclusiveVar):
            visited_path[node.lvalue] = 1
        visited_path[node.unique_id] = visited_path.get(node.unique_id, 0) + 1

        new_edge: ir.Edge = ir.NonClockedEdge(
            unique_id=f"{edge.unique_id}_optimal_{self.make_unique()}"
        )
        if isinstance(node, ir.IfElseNode):
            new_edge.child = ir.IfElseNode(
                unique_id=f"{node.unique_id}_optimal_{self.make_unique()}",
                condition=backwards_replace(node.condition, old_mapping),
                true_edge=self.apply_recursive(
                    edge=node.true_edge,
                    new_mapping=copy.copy(new_mapping),
                    old_mapping=copy.copy(old_mapping),
                    visited_path=copy.copy(visited_path),
                ),
                false_edge=self.apply_recursive(
                    edge=node.false_edge,
                    new_mapping=copy.copy(new_mapping),
                    old_mapping=copy.copy(old_mapping),
                    visited_path=copy.copy(visited_path),
                ),
            )
        elif isinstance(node, ir.AssignNode):
            new_rvalue = backwards_replace(node.rvalue, old_mapping)
            new_mapping[node.lvalue] = new_rvalue
            assert guard(node.child, ir.Edge)
            unique_id = f"{node.unique_id}_optimal_{self.make_unique()}"
            new_edge.child = ir.AssignNode(
                unique_id=unique_id,
                lvalue=node.lvalue,
                rvalue=new_rvalue,
                child=self.apply_recursive(
                    edge=node.child,
                    new_mapping=new_mapping,
                    old_mapping=old_mapping,
                    visited_path=visited_path,
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
    ) -> None:
        """
        Optimizes a node, by increasing amount of work done in a cycle.
        Creates an optimal path that maximizes nonclocked edges.
        """
        assert guard(root, ir.Node)
        logging.debug("%s on %s", self.apply.__name__, root)

        if root.unique_id in self.visited:
            return
        self.visited.add(root.unique_id)

        if isinstance(root, ir.BasicNode):
            mapper: dict[ir.Var, ir.Expression] = {}
            visited_path: dict[Union[ir.Var, str], int] = {}
            if isinstance(root, ir.AssignNode):
                mapper[root.lvalue] = root.rvalue
                if isinstance(root.lvalue, ir.ExclusiveVar):
                    visited_path[root.lvalue] = 1
            assert guard(root.child, ir.Edge)
            assert guard(root.child.child, ir.Node)
            root.optimal_child = self.apply_recursive(
                root.child, mapper, {}, visited_path
            )
        elif isinstance(root, ir.IfElseNode):
            root.optimal_true_edge = self.apply_recursive(root.true_edge, {}, {}, {})
            root.optimal_false_edge = self.apply_recursive(root.false_edge, {}, {}, {})
        elif isinstance(root, ir.DoneNode):
            pass
        else:
            raise RuntimeError(f"{type(root)}")
