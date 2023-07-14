from ..frontend.utils import Lines, Indent
from .. import backend as vast


class Verilog:
    """
    Code generator for verilog that outputs to Lines
    """

    def __init__(self: vast.Case):
        pass

    def from_subsitution(node: vast.Subsitution):
        """
        To Verilog Lines
        """
        assert isinstance(node.type, str), "Subclasses need to set self.type"
        itself = f"{node.lvalue} {node.type} {node.rvalue};"
        lines = Lines(itself)
        if node.appended:
            for stmt in node.appended:
                lines.concat(stmt.to_lines())
        return lines

    def from_declaration(node: vast.Declaration):
        """
        To Verilog Lines
        """
        string = ""
        if node.is_reg:
            string += "reg"
        else:
            string += "wire"
        if node.is_signed:
            string += " signed"
        string += f" [{node.size-1}:0]"
        string += f" {node.name}"
        string += ";"
        return Lines(string)

    def from_case(node: vast.Case):
        """
        To Verilog
        """

        def from_case_item(self: vast.CaseItem):
            """
            To Verilog lines
            """
            lines = Lines()
            lines += f"{self.condition.to_string()}: begin"
            for stmt in self.statements:
                lines.concat(stmt.to_lines(), indent=1)
            lines += "end"
            return lines

        lines = Lines()
        lines += f"case ({node.condition.to_string()})"
        for case_item in node.case_items:
            lines.concat(from_case_item(case_item), indent=1)
        lines += "endcase"
        return lines

    def from_if(node: vast.IfElse):
        """
        To Verilog
        """
        lines = Lines()
        lines += f"if ({node.condition.to_string()}) begin"
        for stmt in node.then_body:
            lines.concat(stmt.to_lines(), indent=1)
        lines += "end else begin"
        for stmt in node.else_body:
            lines.concat(stmt.to_lines(), indent=1)
        lines += "end"
        return lines
