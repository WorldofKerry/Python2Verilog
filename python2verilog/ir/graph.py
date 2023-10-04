"""
Graph representation of the logic

Naming convention:
Vertex
Edge
Element := Vertex | Edge
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Generator, Iterator, Optional, Union

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from python2verilog.utils.generics import GenericRepr, GenericReprAndStr

from ..utils.typed import guard, typed, typed_list, typed_strict
from . import expressions as expr


def get_variables(exp: expr.Expression) -> Iterator[expr.Var]:
    """
    Gets variables from expression
    """
    if isinstance(exp, expr.UBinOp):
        yield from get_variables(exp.left)
        yield from get_variables(exp.right)
    elif isinstance(exp, expr.UnaryOp):
        yield from get_variables(exp.expr)
    elif isinstance(exp, expr.Var):
        yield exp
    elif isinstance(exp, (expr.UInt, expr.Int)):
        pass
    else:
        raise RuntimeError(f"{type(exp)}")


class Element:
    """
    Element, base class for vertex or edge
    """

    def __init__(self, unique_id: str, name: str = ""):
        self._name = typed_strict(name, str)
        self._id = typed_strict(unique_id, str)

    def nonclocked_children(self) -> Iterator[Element]:
        """
        Yields self and optimal nonclocked children of element

        :return: [children_branch_0, children_branch_1, ...]
        """
        logging.debug(f"Non-over-written {type(self)}")
        yield from ()

    def to_string(self):
        """
        To string
        """
        return self._name

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
        self._id = typed_strict(value, str)

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

    def variables(self) -> Iterator[expr.Var]:
        """
        Yields all variables and their nonclcoked children
        """
        yield from ()


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
        self._child = typed(child, Element)
        self._optimal_child: Optional[Element] = None

    def nonclocked_children(self) -> Iterator[Element]:
        if isinstance(self, ClockedEdge):
            yield self
            yield self.optimal_child
        else:
            yield self
            yield from self.optimal_child.nonclocked_children()

    @property
    def child(self) -> Element:
        """
        child or optimal_child if no child
        """
        return typed_strict(self._child, Element)

    @child.setter
    def child(self, other: Element):
        self._child = typed_strict(other, Element)

    def get_all_children(self):
        """
        Gets edges
        """
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
        self._optimal_child = typed_strict(other, Element)


class Node(Element):
    """
    Vertex
    """


class IfElseNode(Node, Element):
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
        self._true_edge = typed_strict(true_edge, Edge)
        self._false_edge = typed_strict(false_edge, Edge)
        self._condition = typed_strict(condition, expr.Expression)
        self._optimal_true_edge: Optional[Edge] = None
        self._optimal_false_edge: Optional[Edge] = None

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
    def true_edge(self, other: Edge):
        self._true_edge = typed_strict(other, Edge)

    @property
    def false_edge(self):
        """
        false edge or optimal false edge if no false edge
        """
        return self._false_edge

    @false_edge.setter
    def false_edge(self, other: Edge):
        self._false_edge = typed_strict(other, Edge)

    @property
    def optimal_true_edge(self):
        """
        optimal true edge or edge otherwise
        """
        return self._optimal_true_edge if self._optimal_true_edge else self._true_edge

    @optimal_true_edge.setter
    def optimal_true_edge(self, other: Edge):
        self._optimal_true_edge = typed_strict(other, Edge)

    @property
    def optimal_false_edge(self):
        """
        optimal false edge
        """
        return (
            self._optimal_false_edge if self._optimal_false_edge else self._false_edge
        )

    @optimal_false_edge.setter
    def optimal_false_edge(self, other: Edge):
        self._optimal_false_edge = typed_strict(other, Edge)

    def get_all_children(self) -> Iterator[Edge]:
        """
        Gets edges
        """
        if self._true_edge:
            yield self._true_edge
        if self._false_edge:
            yield self._false_edge
        if self._optimal_true_edge:
            yield self._optimal_true_edge
        if self._optimal_false_edge:
            yield self._optimal_false_edge

    def get_optimal_children(self):
        """
        Gets optimal children
        """
        assert self._optimal_true_edge and self._optimal_false_edge
        return [self._optimal_true_edge, self._optimal_false_edge]

    def variables(self):
        yield from get_variables(self.condition)
        yield from self.optimal_true_edge.variables()
        yield from self.optimal_false_edge.variables()

    def __repr__(self):
        return f"If({self.condition})"

    def nonclocked_children(self) -> Iterator[Element]:
        yield self
        yield from self.optimal_true_edge.nonclocked_children()
        yield from self.optimal_false_edge.nonclocked_children()


class AssignNode(Node, BasicElement):
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
        self._child = child
        self._lvalue = typed_strict(lvalue, expr.Expression)
        self._rvalue = typed_strict(rvalue, expr.Expression)

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
        self._rvalue = typed_strict(rvalue, expr.Expression)

    def to_string(self):
        """
        To string
        """
        return f"{self._lvalue.to_string()} <= {self._rvalue.to_string()}"

    def verilog(self):
        """
        To string
        """
        return f"{self._lvalue.verilog()} <= {self._rvalue.verilog()}"

    def __repr__(self):
        return f"{self.lvalue} = {self.rvalue}"

    def variables(self):
        yield from get_variables(self.lvalue)
        yield from get_variables(self.rvalue)
        yield from self.child.variables()


class YieldNode(Node, BasicElement):
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
        self._stmts = typed_list(stmts, expr.Expression)

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
        string = "yield ["
        for stmt in self._stmts:
            string += stmt.to_string() + ", "
        string = string[:-2] + "]"
        return string

    def variables(self) -> Iterator[expr.Var]:
        for exp in self.stmts:
            yield from get_variables(exp)

    def __repr__(self) -> str:
        return f"{self.to_string()}"


class DoneNode(Node, Element):
    """
    Signals done
    """

    def __repr__(self) -> str:
        return "Done"


class Edge(BasicElement):
    """
    Represents an edge between two vertices
    """

    def __init__(self, unique_id: str, *args, child: Element | None = None, **kwargs):
        super().__init__(unique_id, *args, child=child, **kwargs)
        self._child = child

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

    def variables(self):
        yield from self.child.variables()

    def __repr__(self) -> str:
        return "=>"


class ClockedEdge(Edge):
    """
    Represents a clocked edge,
    i.e. a clock cycle has to pass for the next node to be executed
    """

    def variables(self):
        yield from ()

    def __repr__(self):
        return "=/>"


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
