"""An Intermediate Representation for HDL based on Verilog"""

import warnings
import inspect

from python2verilog.irast.expressions import Expression

from ..utils.string import Lines
from ..utils.assertions import assert_list_elements


class Statement:
    """
    Represents a statements (i.e. a line or a block)
    If used directly, it is treated as a string literal
    """

    def __init__(self, literal: str = None):
        self.literal = literal

    def to_lines(self):
        """
        To Verilog
        """
        return Lines(self.literal)

    def to_string(self):
        """
        To Verilog
        """
        return self.to_lines().to_string()

    def __repr__(self):
        return self.to_string()


def is_valid_append_end_statements(stmt: Statement, statements: list[Statement]):
    """
    Checks if stmt encapsulates other Statements or not
    If it does, it handles the append, otherwise returns false
    # TODO: there should be a subclass/interface for ones that do encapsulate
    """
    if isinstance(stmt, (Case, IfElse)):
        stmt.append_end_statements(assert_list_elements(statements, Statement))
        return True
    return False


class Subsitution(Statement):
    """
    Interface for
    <lvalue> <blocking or nonblocking> <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        assert isinstance(rvalue, str)  # TODO: should eventually take an expression
        assert isinstance(lvalue, str)
        self.lvalue = lvalue
        self.rvalue = rvalue
        self.type = None
        self.appended = []
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        Converts to Verilog
        """
        assert isinstance(self.type, str), "Subclasses need to set self.type"
        itself = f"{self.lvalue} {self.type} {self.rvalue};"
        lines = Lines(itself)
        if self.appended:
            for stmt in self.appended:
                lines.concat(stmt.to_lines())
        return lines


class NonBlockingSubsitution(Subsitution):
    """
    <lvalue> <= <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        super().__init__(lvalue, rvalue, *args, **kwargs)
        self.type = "<="


class BlockingSubsitution(Subsitution):
    """
    <lvalue> = <rvalue>
    """

    def __init__(self, lvalue: str, rvalue: str, *args, **kwargs):
        super().__init__(lvalue, rvalue, *args, *kwargs)
        self.type = "="


class Declaration(Statement):
    """
    <reg or wire> <modifiers> <[size-1:0]> <name>;
    """

    def __init__(
        self,
        name: str,
        *args,
        size: int = 32,
        is_reg: bool = False,
        is_signed: bool = False,
        **kwargs,
    ):
        self.size = size
        self.is_reg = is_reg
        self.is_signed = is_signed
        self.name = name
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        To Verilog lines
        """
        string = ""
        if self.is_reg:
            string += "reg"
        else:
            string += "wire"
        if self.is_signed:
            string += " signed"
        string += f" [{self.size-1}:0]"
        string += f" {self.name}"
        string += ";"
        return Lines(string)


class CaseItem:
    """
    Verilog case item, i.e.
    <condition>: begin
        <statements>
    end
    """

    def __init__(self, condition: Expression, statements: list[Statement]):
        assert isinstance(condition, Expression)
        self.condition = condition  # Can these by expressions are only literals?
        if statements:
            for stmt in statements:
                assert isinstance(stmt, Statement), f"unexpected {type(stmt)}"
            self.statements = statements
        else:
            self.statements = []

    def to_lines(self):
        """
        To Verilog lines
        """
        lines = Lines()
        lines += f"{self.condition.to_string()}: begin"
        for stmt in self.statements:
            lines.concat(stmt.to_lines(), indent=1)
        lines += "end"
        return lines

    def to_string(self):
        """
        To Verilog
        """
        return self.to_lines().to_string()

    def append_end_statements(self, statements: list[Statement]):
        """
        Append statements to case item
        """
        if not is_valid_append_end_statements(self.statements[-1], statements):
            self.statements = self.statements + assert_list_elements(
                statements, Statement
            )
        return self


class Case(Statement):
    """
    Verilog case statement with various cases
    case (<expression>)
        <items[0]>
        ...
        <items[n]>
    endcase
    """

    def __init__(
        self, expression: Expression, case_items: list[CaseItem], *args, **kwargs
    ):
        assert isinstance(expression, Expression)
        self.condition = expression
        if case_items:
            for item in case_items:
                assert isinstance(item, CaseItem)
            self.case_items = case_items
        else:
            self.case_items = []
        super().__init__(*args, **kwargs)

    def to_lines(self):
        """
        To Verilog Lines
        """
        lines = Lines()
        lines += f"case ({self.condition.to_string()})"
        for item in self.case_items:
            lines.concat(item.to_lines(), indent=1)
        lines += "endcase"
        return lines

    def append_end_statements(self, statements: list[Statement]):
        """
        Adds statements to the last case item
        """
        self.case_items[-1].append_end_statements(
            assert_list_elements(statements, Statement)
        )
        return self


class IfElse(Statement):
    """
    If Else
    """

    def __init__(
        self,
        condition: Expression,
        then_body: list[Statement],
        else_body: list[Statement],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.condition = condition
        self.then_body = assert_list_elements(then_body, Statement)
        self.else_body = assert_list_elements(else_body, Statement)

    def to_lines(self):
        lines = Lines()
        lines += f"if ({self.condition.to_string()}) begin"
        for stmt in self.then_body:
            lines.concat(stmt.to_lines(), indent=1)
        lines += "end else begin"
        for stmt in self.else_body:
            lines.concat(stmt.to_lines(), indent=1)
        lines += "end"
        return lines

    def append_end_statements(self, statements: list[Statement]):
        """
        Appends statements to both branches
        """
        statements = assert_list_elements(statements, Statement)
        # warnings.warn("appending " + statements[0].to_string())
        # if len(statements) > 1:
        #     warnings.warn(statements[1].to_string())
        if not is_valid_append_end_statements(self.then_body[-1], statements):
            self.then_body = self.then_body + statements
        if not is_valid_append_end_statements(self.else_body[-1], statements):
            self.else_body = self.else_body + statements
        return self


class WhileWrapper(Case):
    """
    A while case statement

    Case (WHILE)
        0: if (!<conditional>)
                <continue>
            else
                <loop body / go state 1>
        1: <loop body>
    """

    def append_end_statements(self, statements: list[Statement]):
        """
        While statements have a special case structure,
        where their first case always contains an if statement
        """
        statements = assert_list_elements(statements, Statement)
        assert isinstance(self.case_items[0], CaseItem)
        assert isinstance(self.case_items[0].statements[0], IfElse)
        self.case_items[0].statements[0].then_body = (
            self.case_items[0].statements[0].then_body + statements
        )
        return self


class IfElseWrapper(Case):
    """
    A if-else case statement

    case (<state_name>)

        0: IfElse type (condition check)

        1: <then body>

        2: <else body>

    endcase
    """

    def __init__(
        self, expression: Expression, case_items: list[CaseItem], *args, **kwargs
    ):
        assert len(case_items) == 3
        assert len(case_items[0].statements) == 1
        assert isinstance(case_items[0].statements[0], IfElse)
        super().__init__(expression, case_items, *args, **kwargs)
