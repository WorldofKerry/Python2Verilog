"""
Graph representation of the logic

Naming convention:
Vertex
Edge
Element := Vertex | Edge
"""

from __future__ import annotations

from typing import Optional

from ..utils.assertions import get_typed, get_typed_list
from . import expressions as expr


class Element:
    """
    Element, base class for vertex or edge
    """

    def __init__(self, unique_id: str, name: str = ""):
        self._name = get_typed(name, str)
        self._id = get_typed(unique_id, str)

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

    def __eq__(self, __value: object):
        if isinstance(__value, Element):
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
        self._id = get_typed(value, str)

    def get_all_children(self):
        """
        Gets children
        """
        return []

    def get_optimal_children(self):
        """
        Gets optimal children
        """
        return []

    @property
    def children(self):
        """
        Gets children
        """
        return self.get_all_children()

    @property
    def name(self):
        """
        Gets name
        """
        return self._name


class BasicElement(Element):
    """
    Basic element with a single child
    """

    def __init__(
        self,
        unique_id: str,
        *args,
        child: Optional[Element] = None,
        **kwargs,
    ):
        super().__init__(unique_id, *args, **kwargs)
        self._child = get_typed(child, Element)
        self._optimal_child = None

    @property
    def child(self):
        """
        child or optimal_child if no child
        """
        return self._child

    @child.setter
    def child(self, other: Element):
        self._child = get_typed(other, Element)

    def get_all_children(self):
        """
        Gets edges
        """
        # if self.optimal_child:
        #     return [self.optimal_child]
        # print(f"getting children basicnode {self._optimal_child}")
        # return [self.child]

        children = []
        if self._child:
            children.append(self._child)
        if self._optimal_child:
            children.append(self._optimal_child)
        return children

    def get_optimal_children(self):
        """
        Gets optimal children
        """
        assert self._optimal_child
        return [self._optimal_child]

    @property
    def optimal_child(self):
        """
        Optimal child or child otherwise
        """
        return self._optimal_child if self._optimal_child else self._child

    @optimal_child.setter
    def optimal_child(self, other: Element):
        self._optimal_child = get_typed(other, Element)


class Vertex(Element):
    """
    Vertex
    """


class IfElseNode(Vertex, Element):
    """
    Represents an if-else statement
    """

    def __init__(
        self,
        unique_id: str,
        *args,
        true_edge: Optional[Edge] = None,
        false_edge: Optional[Edge] = None,
        condition: Optional[expr.Expression],
        **kwargs,
    ):
        super().__init__(unique_id, *args, **kwargs)
        self._true_edge = get_typed(true_edge, Edge)
        self._false_edge = get_typed(false_edge, Edge)
        self._condition = get_typed(condition, expr.Expression)
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
        true edge or optimal if no edge
        """
        return self._true_edge

    @true_edge.setter
    def true_edge(self, other: Element):
        self._true_edge = get_typed(other, Element)

    @property
    def false_edge(self):
        """
        false edge or optimal false edge if no false edge
        """
        return self._false_edge

    @false_edge.setter
    def false_edge(self, other: Element):
        self._false_edge = get_typed(other, Element)

    @property
    def optimal_true_edge(self):
        """
        optimal true edge or edge otherwise
        """
        return self._optimal_true_edge if self._optimal_true_edge else self._true_edge

    @optimal_true_edge.setter
    def optimal_true_edge(self, other: Element):
        self._optimal_true_edge = get_typed(other, Element)

    @property
    def optimal_false_edge(self):
        """
        optimal false edge
        """
        return (
            self._optimal_false_edge if self._optimal_false_edge else self._false_edge
        )

    @optimal_false_edge.setter
    def optimal_false_edge(self, other: Element):
        self._optimal_false_edge = get_typed(other, Element)

    def get_all_children(self):
        """
        Gets edges
        """
        # if self._optimal_false_edge and self._optimal_true_edge:
        #     return [self.optimal_true_edge, self.optimal_false_edge]
        # print(
        #     f"returning unoptimized {self._optimal_true_edge} {self._optimal_false_edge}"
        # )
        # return [self.then_edge, self.else_edge]

        children = []
        if self._true_edge:
            children.append(self._true_edge)
        if self._false_edge:
            children.append(self._false_edge)
        if self._optimal_true_edge:
            children.append(self._optimal_true_edge)
        if self._optimal_false_edge:
            children.append(self._optimal_false_edge)
        return children

    def get_optimal_children(self):
        """
        Gets optimal children
        """
        assert self._optimal_true_edge and self._optimal_false_edge
        return [self._optimal_true_edge, self._optimal_false_edge]


class AssignNode(Vertex, BasicElement):
    """
    Represents a non-blocking assignment,
    i.e. assignments that do not block the execution of
    the next statements, without a clock cycle having to pass
    """

    def __init__(
        self,
        unique_id: str,
        *args,
        lvalue: expr.Expression,
        rvalue: expr.Expression,
        child: Optional[Edge] = None,
        **kwargs,
    ):
        super().__init__(unique_id, *args, child=child, **kwargs)
        self._lvalue = get_typed(lvalue, expr.Expression)
        self._rvalue = get_typed(rvalue, expr.Expression)

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
    def rvalue(self, rvalue: expr.Expression):
        self._rvalue = get_typed(rvalue, expr.Expression)

    def to_string(self):
        """
        To string
        """
        return f"{self._lvalue.to_string()} <= {self._rvalue.to_string()}"


class YieldNode(Vertex, BasicElement):
    """
    Yield statement, represents output
    """

    def __init__(
        self,
        unique_id: str,
        name: str = "",
        stmts: Optional[list[expr.Expression]] = None,
        edge: Optional[Edge] = None,
    ):
        super().__init__(unique_id, name=name, child=edge)
        self._stmts = get_typed_list(stmts, expr.Expression)

    @property
    def stmts(self):
        """
        Yield statements
        """
        return self._stmts

    def to_string(self):
        """
        To string
        """
        return f"yield {str(self._stmts)}"


class DoneNode(Vertex, Element):
    """
    Signals done
    """


class Edge(BasicElement):
    """
    Represents an edge between two vertices
    """

    def __init__(self, unique_id: str, *args, child: Element | None = None, **kwargs):
        assert not isinstance(child, Edge)
        super().__init__(unique_id, *args, child=child, **kwargs)

    def to_string(self):
        """
        To string
        """
        if self._name:
            return f"{self._name}"
        return "Next"

    def __str__(self):
        return self.to_string()

    def get_name(self):
        """
        Gets edge name
        """
        return self._name


class NonClockedEdge(Edge):
    """
    Represents a non-clocked edge,
    i.e. no clock cycle has to pass for the next node to be executed
    """


class ClockedEdge(Edge):
    """
    Represents a clocked edge,
    i.e. a clock cycle has to pass for the next node to be executed
    """


def create_networkx_adjacency_list(node: Element):
    """
    Creates adjacency list from a node

    Assumes names are unique
    """
    adjacency_list = {}

    def traverse_graph(curr_node: Element, visited: set[Element]):
        if not curr_node:
            return

        nonlocal adjacency_list
        if curr_node in visited:
            return

        visited.add(curr_node)
        children = curr_node.get_all_children()
        adjacency_list[curr_node] = children

        for child in children:
            traverse_graph(child, visited)

    traverse_graph(node, set())
    return adjacency_list


def create_cytoscape_elements(node: Element):
    """
    Creates adjacency list from a node

    Assumes names are unique
    """
    nodes = []
    edges = []

    def traverse_graph(curr_node: Element, visited: set[str]):
        if not curr_node:
            return

        nonlocal nodes
        if curr_node.unique_id in visited:
            return

        visited.add(curr_node.unique_id)
        children = curr_node.get_all_children()
        # optimal_children = curr_node.get_optimal_children()

        if not isinstance(curr_node, Edge):
            nodes.append(
                {
                    "data": {
                        "id": curr_node.unique_id,
                        "label": str(curr_node),
                        "class": str(curr_node.__class__.__name__),
                    }
                }
            )
            for child in curr_node.children:
                edges.append(
                    {
                        "data": {
                            "source": curr_node.unique_id,
                            "target": child.child.unique_id,
                            "class": str(child.__class__.__name__),
                            "label": str(child),
                        }
                    }
                )

            for child in children:
                traverse_graph(child.child, visited)

    traverse_graph(node, set())
    return {"nodes": nodes, "edges": edges}
