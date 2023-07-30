"""
Graph representation of the logic
"""

from __future__ import annotations
import copy

from python2verilog.ir.expressions import Optional
from python2verilog.ir.statements import Optional

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
        items = [f"{key}=({value})" for key, value in self.__dict__.items()]
        return f"{self.__class__.__name__}({','.join(items)})"

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Node):
            return self._id == __value._id
        return False

    @property
    def unique_id(self):
        """
        Gets node id
        """
        return self._id

    @unique_id.setter
    def unique_id(self, value):
        """
        Sets node id
        """
        self._id = assert_type(value, str)

    def get_children(self):
        """
        Gets children
        """
        return []

    @property
    def children(self):
        """
        Gets children
        """
        return self.get_children()

    @property
    def name(self):
        """
        Gets name
        """
        return self._name


class IfElseNode(Node):
    """
    Represents an if-else statement
    """

    def __init__(
        self,
        unique_id: str,
        *args,
        true_edge: Optional[Edge] = None,
        false_edge: Optional[Edge] = None,
        condition: Optional[Expression],
        **kwargs,
    ):
        super().__init__(unique_id, *args, **kwargs)
        self._true_edge = assert_type(true_edge, Edge)
        self._false_edge = assert_type(false_edge, Edge)
        self._condition = assert_type(condition, Expression)
        self._optimal_true_edge = None
        self._optimal_false_edge = None

    def to_string(self):
        """
        To string
        """
        return f"if ({self._condition.to_string()})"

    @property
    def condition(self):
        """
        conditional
        """
        return self._condition

    @property
    def true_edge(self):
        """
        true edge
        """
        return self._true_edge

    @true_edge.setter
    def true_edge(self, other: Node):
        self._true_edge = assert_type(other, Node)

    @property
    def false_edge(self):
        """
        false edge
        """
        return self._false_edge

    @false_edge.setter
    def false_edge(self, other: Node):
        self._false_edge = assert_type(other, Node)

    @property
    def optimal_true_edge(self):
        """
        optimal true edge
        """
        return self._optimal_true_edge

    @optimal_true_edge.setter
    def optimal_true_edge(self, other: Node):
        self._optimal_true_edge = assert_type(other, Node)

    @property
    def optimal_false_edge(self):
        """
        optimal false edge
        """
        return self._optimal_false_edge

    @optimal_false_edge.setter
    def optimal_false_edge(self, other: Node):
        self._optimal_false_edge = assert_type(other, Node)

    def get_children(self):
        """
        Gets edges
        """
        # if self._optimal_false_edge and self._optimal_true_edge:
        #     return [self.optimal_true_edge, self.optimal_false_edge]
        # print(
        #     f"returning unoptimized {self._optimal_true_edge} {self._optimal_false_edge}"
        # )
        # return [self.then_edge, self.else_edge]

        children = [self.true_edge, self.false_edge]
        if self.optimal_true_edge:
            children.append(self.optimal_true_edge)
        if self.optimal_false_edge:
            children.append(self.optimal_false_edge)
        return children


class BasicNode(Node):
    """
    Basic node with a single edge
    """

    def __init__(
        self,
        unique_id: str,
        *args,
        child: Optional[Node] = None,
        **kwargs,
    ):
        super().__init__(unique_id, *args, **kwargs)
        self._child = assert_type(child, Node)
        self._optimal_child = None

    @property
    def child(self):
        """
        child
        """
        return self._child

    @child.setter
    def child(self, other: Node):
        self._child = assert_type(other, Node)

    def get_children(self):
        """
        Gets edges
        """
        # if self.optimal_child:
        #     return [self.optimal_child]
        # print(f"getting children basicnode {self._optimal_child}")
        # return [self.child]

        children = [self.child]
        if self.optimal_child:
            children.append(self.optimal_child)
        return children

    def set_edge(self, edge: Node):
        """
        Adds an edge
        """
        self.child = edge
        return self.child

    @property
    def optimal_child(self):
        """
        Optimal child
        """
        return self._optimal_child

    @optimal_child.setter
    def optimal_child(self, other: Node):
        self._optimal_child = assert_type(other, Node)


class AssignNode(BasicNode):
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
        child: Optional[Edge] = None,
        **kwargs,
    ):
        super().__init__(unique_id, *args, child=child, **kwargs)
        self._lvalue = assert_type(lvalue, Expression)
        self._rvalue = assert_type(rvalue, Expression)

    @property
    def lvalue(self):
        """
        lvalue
        """
        return self._lvalue

    @property
    def rvalue(self):
        """
        rvalue
        """
        return self._rvalue

    @rvalue.setter
    def rvalue(self, rvalue: Expression):
        self._rvalue = assert_type(rvalue, Expression)

    def to_string(self):
        """
        To string
        """
        return f"{self._lvalue.to_string()} <= {self._rvalue.to_string()}"


class YieldNode(BasicNode):
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
        super().__init__(unique_id, name=name, child=edge)
        self._stmts = assert_list_type(stmts, Expression)

    def to_string(self):
        """
        To string
        """
        return f"yield {str(self._stmts)}"

    def __str__(self):
        """
        to string
        """
        return "\n".join([f"out{i} <= {str(v)}" for i, v in enumerate(self._stmts)])


class DoneNode(Node):
    """
    Signals done
    """

    def __init__(self, unique_id: str, name: str = ""):
        super().__init__(unique_id, name)


class Edge(BasicNode):
    """
    Represents an edge between two nodes
    """

    def __init__(self, unique_id: str, *args, child: Optional[Node] = None, **kwargs):
        super().__init__(unique_id, child=child, *args, **kwargs)

    def to_string(self):
        """
        To string
        """
        if self._name:
            return f"{self._name}, normal"
        return "Next, normal"

    def __str__(self):
        return self.to_string()

    def get_name(self):
        """
        Gets edge name
        """
        return self._name

    def get_next_node(self):
        """
        Gets next node
        """
        return self._child

    def get_children(self):
        """
        Gets children
        """
        return [self.get_next_node()]


class NonClockedEdge(Edge):
    """
    Represents a non-clocked edge,
    i.e. no clock cycle has to pass for the next node to be executed
    """

    def __init__(self, unique_id: str, *args, **kwargs):
        super().__init__(unique_id, *args, **kwargs)

    def to_string(self):
        if self._name:
            return f"{self.name}, nonclocked"
        return f"Next, nonclocked"


class ClockedEdge(Edge):
    """
    Represents a clocked edge,
    i.e. a clock cycle has to pass for the next node to be executed
    """

    def __init__(self, unique_id: str, *args, **kwargs):
        super().__init__(unique_id, *args, **kwargs)


def create_networkx_adjacency_list(node: Node):
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
        adjacency_list[curr_node] = list(children)

        for child in children:
            traverse_graph(child, visited)

    traverse_graph(node, set())
    return adjacency_list


def create_cytoscape_elements(node: Node):
    """
    Creates adjacency list from a node

    Assumes names are unique
    """
    elements = []

    def traverse_graph(curr_node: Node, visited: set[Node]):
        if not curr_node:
            return

        nonlocal elements
        if curr_node in visited:
            return

        visited.add(curr_node)
        children = curr_node.get_children()
        # print(f"getting children {curr_node} {children}")
        elements.append({"data": {"id": curr_node.unique_id, "label": str(curr_node)}})
        for child in curr_node.children:
            elements.append(
                {"data": {"source": curr_node.unique_id, "target": child.unique_id}}
            )

        for child in children:
            traverse_graph(child, visited)

    traverse_graph(node, set())
    return elements
