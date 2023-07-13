"""Verilog Abstract Syntax Tree Components"""

from ..frontend.utils import Lines
import warnings


def assert_list_elements(the_list: list, elem_type):
    """
    Asserts that all elems in the list are of elem_type, then returns the list
    """
    if the_list:
        for elem in the_list:
            assert isinstance(elem, elem_type)
        return the_list
    return []


class Expression:
    """
    Verilog expression, e.g.
    a + b
    Currently just a string
    """

    def __init__(self, string: str):
        self.string = string

    def to_string(self):
        """
        To Verilog
        """
        return self.string


class Statement:
    """
    Represents a statement in verilog (i.e. a line or a block)
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

    # def append_end_statements(self, statements: list):
    #     warnings.warn("append_end_statements on base class")
    #     self.literal += str(statements)


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
        self.appended = None
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

    def append_end_statements(self, statements: list[Statement]):
        self.appended = assert_list_elements(statements, Statement)
        return self


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
        return self.to_lines().to_string()

    def append_end_statements(self, statements: list[Statement]):
        """
        Append statements to case item
        """
        # self.statements = self.statements + assert_list_elements(statements, Statement)
        self.statements[-1].append_end_statements(
            assert_list_elements(statements, Statement)
        )
        # warnings.warn(statements[0].to_string())
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
            case_items = []
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
    Verilog if else
    """

    def __init__(
        self,
        condition: Expression,
        then_body: list[Statement],
        else_body: list[Statement],
    ):
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
        self.then_body[-1].append_end_statements(statements)
        self.else_body[-1].append_end_statements(statements)
        return self


class While(IfElse):
    """
    Abstract While wrapper
    """

    def append_end_statements(self, statements: list[Statement]):
        """
        Appends statements to both end branch
        """
        statements = assert_list_elements(statements, Statement)
        # warnings.warn("appending " + statements[0].to_string())
        # if len(statements) > 1:
        #     warnings.warn(statements[1].to_string())
        self.then_body[-1].append_end_statements(statements)
        return self
