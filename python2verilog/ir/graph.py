"""
Graph representation of the logic
"""

from __future__ import annotations
from .statements import *
from .expressions import *
from ..utils.assertions import assert_list_type, assert_type


class Node:
    """
    Represents logic
    """

    def __init__(self, name: str = ""):
        self.name = assert_type(name, str)

    def to_string(self):
        """
        To string
        """
        return f"name: {self.name}"

    def __str__(self):
        return self.to_string()


class IfElseNode(Node):
    """
    Represents an if-else statement
    """

    def __init__(
        self,
        *args,
        true_branch: Optional[Edge] = None,
        false_branch: Optional[Edge] = None,
        condition: Optional[Expression],
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.true_branch = assert_type(true_branch, Edge)
        self.false_branch = assert_type(false_branch, Edge)
        self.condition = assert_type(condition, Expression)

    def to_string(self):
        """
        To string
        """
        return (
            super().to_string()
            + f", if {self.condition.to_string()} then: \
                {self.true_branch.to_string()} else: {self.false_branch.to_string()}"
        )


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
        edge: Edge,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.lvalue = assert_type(lvalue, Expression)
        self.rvalue = assert_type(rvalue, Expression)
        self.edge = assert_type(edge, Edge)

    def to_string(self):
        """
        To string
        """
        return (
            super().to_string()
            + f", lvalue: {self.lvalue.to_string()} rvalue: {self.rvalue.to_string()}"
        )


class Edge:
    """
    Represents an edge between two nodes
    """

    def __init__(self, name: str = ""):
        self.name = assert_type(name, str)

    def to_string(self):
        """
        To string
        """
        return f"name: {self.name}"

    def __str__(self):
        return self.to_string()


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
