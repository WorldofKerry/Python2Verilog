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

    def __init__(self, unique_id: str, name: str = ""):
        self._name = assert_type(name, str)
        self._id = assert_type(unique_id, str)

    def to_string(self):
        """
        To string
        """
        return self._name

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return f"{self.__class__.__name__} name: ({self._name})"

    def get_children(self):
        """
        Gets edges
        """
        return []

    def get_name(self):
        """
        Gets node name
        """
        return self._name

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Node):
            return self._id == __value._id
        return False


class IfElseNode(Node):
    """
    Represents an if-else statement
    """

    def __init__(
        self,
        unique_id: str,
        *args,
        then_edge: Optional[Edge] = None,
        else_edge: Optional[Edge] = None,
        condition: Optional[Expression],
        **kwargs,
    ):
        super().__init__(unique_id, *args, **kwargs)
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

    def get_children(self):
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
        unique_id: str,
        *args,
        lvalue: Expression,
        rvalue: Expression,
        edge: Optional[Edge] = None,
        **kwargs,
    ):
        super().__init__(unique_id, *args, **kwargs)
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

    def get_children(self):
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


class YieldNode(Node):
    """
    Yield statement, represents output
    """

    def __init__(
        self,
        unique_id: str,
        name: str = "",
        stmts: Optional[list[Expression]] = None,
        edge: Optional[Edge] = None,
    ):
        super().__init__(unique_id, name)
        self._stmts = assert_list_type(stmts, Expression)
        self._edge = assert_type(edge, Edge)

    def to_string(self):
        """
        To string
        """
        return f"yield {self._stmts}"

    def set_edge(self, edge: Edge):
        """
        Adds an edge
        """
        if self._edge:
            raise ValueError(f"reassigning edge {self._edge} to {edge}")
        self._edge = assert_type(edge, Edge)

    def get_children(self):
        """
        Gets edges
        """
        return [copy.deepcopy(self._edge)]


class Edge(Node):
    """
    Represents an edge between two nodes
    """

    def __init__(
        self, unique_id: str, *args, next_node: Optional[Node] = None, **kwargs
    ):
        self._node = assert_type(next_node, Node)
        super().__init__(unique_id, *args, **kwargs)

    def to_string(self):
        """
        To string
        """
        if self._name:
            return self._name
        return "Next"

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return f"{self.__class__.__name__} name: ({self._name}), node: ({self._node})"

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

    def get_children(self):
        return [self.get_next_node()]


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

    def traverse_graph(curr_node: Node, visited: set[Node]):
        if not curr_node:
            return

        nonlocal adjacency_list
        if curr_node in visited:
            return

        visited.add(curr_node)
        children = curr_node.get_children()
        # if children[0] == None:
        #     warnings.warn(f"{str(list(children))} {curr_node}")
        adjacency_list[curr_node] = list(children)

        for child in children:
            traverse_graph(child, visited)

    traverse_graph(node, set())
    return adjacency_list
