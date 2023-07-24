"""
Graph representation of the logic
"""

from __future__ import annotations
import copy

from .statements import *
from .expressions import *
from ..utils.assertions import assert_list_type, assert_type


class Node:
    """
    Represents logic
    """

    def __init__(self, name: str = ""):
        self._name = assert_type(name, str)

    def to_string(self):
        """
        To string
        """
        return self._name

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return f"{self.__class__.__name__} name: ({self._name})"

    def get_edges(self):
        """
        Gets edges
        """
        warnings.warn("get edges on base class Node")
        result: list[Edge] = []
        return result

    def get_name(self):
        """
        Gets node name
        """
        return self._name


class IfElseNode(Node):
    """
    Represents an if-else statement
    """

    def __init__(
        self,
        *args,
        then_edge: Optional[Edge] = None,
        else_edge: Optional[Edge] = None,
        condition: Optional[Expression],
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._then_edge = assert_type(then_edge, Edge)
        self._else_edge = assert_type(else_edge, Edge)
        self._condition = assert_type(condition, Expression)

    def to_string(self):
        """
        To string
        """
        return f"if ({self._condition.to_string()})"

    def __repr__(self):
        return super().__repr__() + f", condition: ({self._condition})"

    def get_edges(self):
        """
        Gets edges
        """
        return [copy.deepcopy(self._then_edge), copy.deepcopy(self._else_edge)]


class AssignNode(Node):
    """
    Represents a non-blocking assignment,
    i.e. assignments that do not block the execution of
    the next statements, without a clock cycle having to pass
    """

    def __init__(
        self,
        *args,
        lvalue: Expression,
        rvalue: Expression,
        edge: Optional[Edge] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._lvalue = assert_type(lvalue, Expression)
        self._rvalue = assert_type(rvalue, Expression)
        self._edge = assert_type(edge, Edge)

    def to_string(self):
        """
        To string
        """
        return f"{self._lvalue.to_string()} <= {self._rvalue.to_string()}"

    def __repr__(self):
        return (
            super().__repr__() + f", lvalue: ({self._lvalue}) rvalue: ({self._rvalue})"
        )

    def get_edges(self):
        """
        Gets edges
        """
        return [copy.deepcopy(self._edge)]

    def set_edge(self, edge: Edge):
        """
        Adds an edge
        """
        if self._edge:
            raise ValueError(f"reassigning edge {self._edge} to {edge}")
        self._edge = assert_type(edge, Edge)


class Edge:
    """
    Represents an edge between two nodes
    """

    def __init__(self, name: str = "", next_node: Optional[Node] = None):
        self._name = assert_type(name, str)
        self._node = assert_type(next_node, Node)

    def to_string(self):
        """
        To string
        """
        if self._name:
            return self._name
        return "Edge"

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return (
            f"{self.__class__.__name__} name: ({self._name}), next node: ({self._node})"
        )

    def set_next_node(self, node: Node):
        """
        Sets next node
        """
        if self._node:
            raise ValueError(f"reassigning node {self._node} to {node}")
        self._node = assert_type(node, Node)

    def get_name(self):
        """
        Gets edge name
        """
        return self._name

    def get_next_node(self):
        """
        Gets next node
        """
        return copy.deepcopy(self._node)


class NonclockedEdge(Edge):
    """
    Represents a non-clocked edge,
    i.e. no clock cycle has to pass for the next node to be executed
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_string(self):
        return super().to_string() + ", nonclocked"


class ClockedEdge(Edge):
    """
    Represents a clocked edge,
    i.e. a clock cycle has to pass for the next node to be executed
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_string(self):
        return super().to_string() + ", clocked"


def create_adjacency_list(node: Node):
    """
    Creates adjacency list from a node

    Assumes names are unique
    """
    adjacency_list = {}

    def traverse_graph(curr_node: Node, visited: set[Node | Edge]):
        nonlocal adjacency_list
        if curr_node in visited:
            return

        visited.add(curr_node)
        edges = curr_node.get_edges()
        adjacency_list[curr_node] = list(edges)

        for edge in edges:
            next_node = edge.get_next_node()
            if next_node:
                adjacency_list[edge] = [next_node]
                traverse_graph(next_node, visited)

    traverse_graph(node, set())
    return adjacency_list
