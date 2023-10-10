"""
The freshest in-order generator parser
"""
import ast as pyast
import itertools
import logging
from typing import Collection, Iterable, Literal, Optional, overload

from python2verilog import ir
from python2verilog.utils.typed import guard, typed_list, typed_strict


class GeneratorFunc:
    """
    In-order generator function parser
    """

    UNDEFINED_EDGE = ir.ClockedEdge(unique_id="UNDEFINED_EDGE")

    def __init__(self, context: ir.Context) -> None:
        self._context = context
        self.UNDEFINED_NODE = ir.AssignNode(
            unique_id="UNDEFINED_NODE",
            lvalue=self._context.state_var,
            rvalue=self._context.state_var,
        )
    
    def create_root(self):
        return self._parse_func()

    def _parse_func(self, prefix: str = "_state"):
        """
        Parses
        """
        breaks, continues = [], []
        body_head, prev_tails = self._parse_stmts(
            self._context.py_ast.body, prefix=prefix, breaks=breaks, continues=continues
        )
        assert len(breaks) == 0
        assert len(continues) == 0
        for tail in prev_tails:
            tail.child = ir.DoneNode(unique_id="_state_done")
        self._context.entry_state = ir.State(body_head.unique_id)

        return body_head, self._context

    def _parse_stmt(
        self,
        stmt: pyast.stmt,
        breaks: list[ir.Edge],
        continues: list[ir.Edge],
        prefix: str,
    ):
        """
        Parses a statement

        :param stmt: statement to-be-parsed
        :param brk: list of edges that connect to end of break stmt
        :param cntnue: where to connect continue edges
        """
        if isinstance(stmt, pyast.Assign):
            return self._parse_assign(assign=stmt, prefix=prefix)
        if isinstance(stmt, pyast.Yield):
            return self._parse_yield(yiel=stmt, prefix=prefix)
        if isinstance(stmt, pyast.Expr):
            return self._parse_stmt(
                stmt=stmt.value, breaks=breaks, continues=continues, prefix=prefix
            )
        if isinstance(stmt, pyast.While):
            return self._parse_while(whil=stmt, prefix=prefix)
        if isinstance(stmt, pyast.Break):
            nothing = ir.AssignNode(
                unique_id=prefix,
                name="break",
                lvalue=self._context.state_var,
                rvalue=self._context.state_var,
                child=ir.ClockedEdge(
                    unique_id=f"{prefix}_e",
                ),
            )
            breaks.append(nothing.child)
            return nothing, []
        if isinstance(stmt, pyast.If):
            return self._parse_ifelse(
                ifelse=stmt, prefix=prefix, breaks=breaks, continues=continues
            )
        return ir.DoneNode(unique_id=str(self._context.done_state)), [
            self.UNDEFINED_EDGE
        ]

    def _parse_stmts(
        self,
        stmts: list[pyast.stmt],
        prefix: str,
        breaks: list[ir.Edge],
        continues: list[ir.Edge],
    ):
        """
        A helper for parsing statements (blocks of code)

        :return: (head, breaks, continues, ends)
        - head is the head of this body (first node in body)
        - ends are edges come from end of body (what to do after body)
        """
        body_head = None
        prev_tails: Optional[list[ir.Edge]] = None
        counter = itertools.count()

        for stmt in stmts:
            head_node, tail_edges = self._parse_stmt(
                stmt=stmt,
                breaks=breaks,
                continues=continues,
                prefix=f"{prefix}{next(counter)}",
            )
            if not body_head:
                body_head = head_node
            if prev_tails:
                for tail in prev_tails:
                    tail.child = head_node
            prev_tails = typed_list(tail_edges, ir.Edge)
            assert guard(head_node, ir.Node)

        return body_head, prev_tails

    def _parse_while(self, whil: pyast.While, prefix: str):
        breaks, continues = [], []
        body_head, ends = self._parse_stmts(
            stmts=whil.body,
            prefix=f"{prefix}_while",
            breaks=breaks,
            continues=continues,
        )
        done_edge = ir.ClockedEdge(unique_id=f"{prefix}_done_e")
        while_head = ir.IfElseNode(
            unique_id=f"{prefix}_while_test",
            condition=self._parse_expression(whil.test),
            true_edge=ir.ClockedEdge(unique_id=f"{prefix}_body_e", child=body_head),
            false_edge=done_edge,
        )
        for cont in continues:
            cont.child = while_head
        for end in ends:
            end.child = while_head
        return while_head, [done_edge, *breaks]

    def _parse_ifelse(
        self,
        ifelse: pyast.If,
        prefix: str,
        breaks: list[ir.Edge],
        continues: list[ir.Edge],
    ):
        then_head, then_ends = self._parse_stmts(
            stmts=ifelse.body,
            prefix=f"{prefix}_ifelse_test",
            breaks=breaks,
            continues=continues,
        )
        to_then = ir.NonClockedEdge(unique_id=f"{prefix}_then_e", child=then_head)

        if ifelse.orelse:
            else_head, else_ends = self._parse_stmts(
                stmts=ifelse.orelse,
                prefix=f"{prefix}_while",
                breaks=breaks,
                continues=continues,
            )
            to_else = ir.NonClockedEdge(unique_id=f"{prefix}_else_e", child=else_head)
            ret = ir.IfElseNode(
                unique_id=prefix,
                condition=self._parse_expression(ifelse.test),
                true_edge=to_then,
                false_edge=to_else,
            )
            return ret, [*then_ends, *else_ends]
        else:
            to_else = ir.NonClockedEdge(unique_id=f"{prefix}_else_e")
            ret = ir.IfElseNode(
                unique_id=prefix,
                condition=self._parse_expression(ifelse.test),
                true_edge=to_then,
                false_edge=to_else,
            )
            return ret, [*then_ends, to_else]

    @staticmethod
    def pprint(elem: ir.Element):
        """
        Get node str
        """
        return str(list(elem.visit_nonclocked()))

    def _parse_yield(self, yiel: pyast.Assign, prefix: str):
        """
        Parse yield
        yield <value>
        """
        if isinstance(yiel.value, pyast.Tuple):
            stmts = [self._parse_expression(c) for c in yiel.value.elts]
        elif isinstance(yiel.value, pyast.expr):
            stmts = [self._parse_expression(yiel.value)]
        else:
            raise TypeError(f"Expected tuple {type(yiel.value)} {pyast.dump(yiel)}")

        # pylint: disable=unpacking-non-sequence
        head, tail = self._weave_nonclocked_edges(
            self._create_assign_nodes(self._context.output_vars, stmts, prefix),
            f"{prefix}_e",
            last_edge=True,
        )
        tail.child = ir.AssignNode(
            unique_id=f"{prefix}_valid",
            lvalue=self._context.signals.valid,
            rvalue=ir.UInt(1),
            child=ir.ClockedEdge(unique_id=f"{prefix}_e"),
        )
        return head, [tail.child.child]

    def _target_value_visitor(self, target: pyast.expr, value: pyast.expr):
        """
        Takes two trees, ensures they're idential,
        then yields the target/value pairs
        """
        if isinstance(value, pyast.Tuple):
            if guard(target, pyast.Name):
                raise TypeError(
                    f"Attempted to assign {target.id} = {pyast.unparse(value)}."
                    " Currently variables can only containt ints."
                )
            assert guard(target, pyast.Tuple)
            assert len(target.elts) == len(value.elts)
            for t, v in zip(target.elts, value.elts):
                yield from self._target_value_visitor(t, v)
        elif isinstance(target, pyast.Name):
            if not self._context.is_declared(target.id):
                self._context.add_global_var(ir.Var(py_name=target.id))
            yield (ir.Var(target.id), self._parse_expression(value))
        else:
            raise TypeError(f"{pyast.dump(target)} {pyast.dump(value)}")

    @staticmethod
    def _create_assign_nodes(
        variables: Collection[ir.ExclusiveVar],
        exprs: Collection[ir.Expression],
        prefix: str,
    ) -> Iterable[ir.AssignNode]:
        """
        Create assign nodes from variables and expressions
        """
        assert len(variables) == len(exprs), f"{variables} {exprs}"
        counters = itertools.count()
        for var, expr, counter in zip(variables, exprs, counters):
            yield ir.AssignNode(
                unique_id=f"{prefix}_assign{counter}", lvalue=var, rvalue=expr
            )

    @overload
    @staticmethod
    def _weave_nonclocked_edges(
        nodes: Iterable[ir.BasicElement], prefix: str, last_edge: Literal[True]
    ) -> tuple[ir.AssignNode, ir.NonClockedEdge]:
        ...

    @overload
    @staticmethod
    def _weave_nonclocked_edges(
        nodes: Iterable[ir.BasicElement], prefix: str, last_edge: Literal[False]
    ) -> tuple[ir.AssignNode, ir.AssignNode]:
        ...

    @staticmethod
    def _weave_nonclocked_edges(nodes, prefix, last_edge):
        """
        Weaves nodes with nonclocked edges.

        If last_edge, then last node is an edge,
        else last node is last assign node.

        :return: (first assign node, last node)
        """
        counters = itertools.count()
        head: Optional[ir.BasicElement] = None
        prev: Optional[ir.BasicElement] = None
        node: ir.BasicElement = ir.BasicElement(unique_id="UNDEFINED")
        for node, counter in zip(nodes, counters):
            if not head:
                head = node
            if prev:
                prev.child = node
            node.child = ir.NonClockedEdge(
                unique_id=f"{prefix}_{counter}",
            )
            prev = node.child
        if last_edge:
            assert guard(head, ir.AssignNode)
            assert guard(prev, ir.NonClockedEdge)
            return head, prev
        assert guard(head, ir.AssignNode)
        assert guard(node, ir.AssignNode)
        return head, node

    def _parse_assign(self, assign: pyast.Assign, prefix: str):
        """
        <target0, target1, ...> = <value>;
        a, b = b, a + b

        target value visitor
        a -> b
        b -> a + b

        create assign nodes
        a = b
        b = a + b

        weave
        a = b
          -> b = a + b
            -> None
        """
        assert len(assign.targets) == 1
        targets, values = zip(
            *self._target_value_visitor(assign.targets[0], assign.value)
        )

        # pylint: disable=unpacking-non-sequence
        head, tail = self._weave_nonclocked_edges(
            self._create_assign_nodes(targets, values, prefix),
            f"{prefix}_e",
            last_edge=False,
        )
        logging.debug("Assign Head %s", list(head.visit_nonclocked()))

        tail.child = ir.ClockedEdge(
            unique_id=f"{prefix}",
        )
        return head, [tail.child]

    def _parse_expression(self, expr: pyast.AST) -> ir.Expression:
        """
        <expression> (e.g. constant, name, subscript, etc., those that return a value)
        """
        if isinstance(expr, pyast.Constant):
            return ir.Int(expr.value)
        if isinstance(expr, pyast.Name):
            return ir.Var(py_name=expr.id)
        if isinstance(expr, pyast.Subscript):
            return self._parse_subscript(expr)
        if isinstance(expr, pyast.BinOp):
            return self._parse_binop(expr)
        if isinstance(expr, pyast.UnaryOp):
            if isinstance(expr.op, pyast.USub):
                return ir.UnaryOp("-", self._parse_expression(expr.operand))
            raise TypeError(
                "Error: unexpected unaryop type", type(expr.op), pyast.dump(expr.op)
            )
        if isinstance(expr, pyast.Compare):
            return self._parse_compare(expr)
        if isinstance(expr, pyast.BoolOp):
            if isinstance(expr.op, pyast.And):
                return ir.UBinOp(
                    self._parse_expression(expr.values[0]),
                    "&&",
                    self._parse_expression(expr.values[1]),
                )
        raise TypeError(
            "Error: unexpected expression type", type(expr), pyast.dump(expr)
        )

    def _parse_subscript(self, node: pyast.Subscript) -> ir.Expression:
        """
        <value>[<slice>]
        Note: built from right to left, e.g. [z] -> [y][z] -> [x][y][z] -> matrix[x][y][z]
        """
        return ir.Expression(
            f"{self._parse_expression(node.value).to_string()}\
                [{self._parse_expression(node.slice).to_string()}]"
        )

    def _parse_compare(self, node: pyast.Compare) -> ir.UBinOp:
        """
        <left> <op> <comparators>
        """
        assert len(node.ops) == 1
        assert len(node.comparators) == 1

        if isinstance(node.ops[0], pyast.Lt):
            return ir.LessThan(
                self._parse_expression(node.left),
                self._parse_expression(node.comparators[0]),
            )
        if isinstance(node.ops[0], pyast.LtE):
            operator = "<="
        elif isinstance(node.ops[0], pyast.Gt):
            operator = ">"
        elif isinstance(node.ops[0], pyast.GtE):
            operator = ">="
        elif isinstance(node.ops[0], pyast.NotEq):
            operator = "!=="
        elif isinstance(node.ops[0], pyast.Eq):
            operator = "==="
        else:
            raise TypeError(
                "Error: unknown operator", type(node.ops[0]), pyast.dump(node.ops[0])
            )
        return ir.BinOp(
            left=self._parse_expression(node.left),
            oper=operator,
            right=self._parse_expression(node.comparators[0]),
        )

    def _parse_binop(self, expr: pyast.BinOp) -> ir.Expression:
        """
        <left> <op> <right>

        With special case for floor division
        """
        if isinstance(expr.op, pyast.Add):
            return ir.Add(
                self._parse_expression(expr.left), self._parse_expression(expr.right)
            )
        if isinstance(expr.op, pyast.Sub):
            return ir.Sub(
                self._parse_expression(expr.left), self._parse_expression(expr.right)
            )

        if isinstance(expr.op, pyast.Mult):
            return ir.Mul(
                self._parse_expression(expr.left), self._parse_expression(expr.right)
            )

        if isinstance(expr.op, pyast.FloorDiv):
            left = self._parse_expression(expr.left)
            right = self._parse_expression(expr.right)
            return ir.FloorDiv(left, right)
        if isinstance(expr.op, pyast.Mod):
            left = self._parse_expression(expr.left)
            right = self._parse_expression(expr.right)
            return ir.Mod(left, right)
        raise TypeError(
            "Error: unexpected binop type", type(expr.op), pyast.dump(expr.op)
        )
