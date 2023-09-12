"""Parses Python Generator Functions to Intermediate Representation"""

from __future__ import annotations

import ast as pyast

from .. import ir
from ..utils.assertions import get_typed, get_typed_list
from ..utils.string import Indent, Lines


def name_to_var(name: pyast.expr) -> ir.Var:
    """
    Converts a pyast.Name to a ir.Var using its id
    """
    assert isinstance(name, pyast.Name)
    return ir.Var(name.id)


class Generator2Graph:
    """
    Parses python generator functions to Verilog AST
    """

    def __init__(
        self,
        context: ir.Context,
        done_state_name: str = "_state_fake",
    ):
        """
        Initializes the parser, does quick setup work
        """
        context.validate()
        self._context = get_typed(context, ir.Context)

        # Populate function calls
        # TODO: lazy-load or infer types
        for node in context.py_ast.body:
            for assign in pyast.walk(node):
                if isinstance(assign, pyast.Assign):
                    for child in pyast.walk(assign):
                        if isinstance(child, pyast.Call):
                            assert len(assign.targets) == 1
                            target = assign.targets[0]
                            assert isinstance(target, pyast.Name)
                            if assign.targets[0] not in self._context.instances:
                                assert isinstance(assign.value, pyast.Call)
                                assert isinstance(assign.value.func, pyast.Name)
                                cxt = self._context.namespace[assign.value.func.id]
                                instance = cxt.create_instance(target.id)
                                self._context.instances[target.id] = instance

        self._root = self.__parse_statements(
            stmts=context.py_ast.body,
            prefix="_state",
            nextt=ir.DoneNode(unique_id=done_state_name, name="done"),
        )

        self._context.entry_state = self._root.unique_id
        self._context.ready_state = done_state_name

    @property
    def root(self):
        """
        Returns the root of the IR Graph
        """
        return self._root

    @property
    def context(self):
        """
        Returns the context surrounding the Python generator function
        """
        return self._context

    @property
    def results(self):
        """
        Returns tuple containing the root and the context
        """
        return (self.root, self.context)

    def __parse_targets(self, nodes: list[pyast.expr]):
        """
        Warning: only single target on left-hand-side supported

        <target0, target1, ...> =
        """
        assert len(nodes) == 1
        node = nodes[0]
        if isinstance(node, pyast.Subscript):
            assert isinstance(node.value, pyast.Name)
            if not self._context.is_declared(node.value.id):
                self._context.add_global_var(ir.Var(py_name=node.value.id))
        elif isinstance(node, pyast.Name):
            if not self._context.is_declared(node.id):
                self._context.add_global_var(ir.Var(py_name=node.id))
        else:
            raise TypeError(f"Unsupported lvalue type {type(node)} {pyast.dump(node)}")
        return self.__parse_expression(node)

    def __parse_assign(
        self, node: pyast.Assign, prefix: str
    ) -> tuple[ir.BasicElement, ir.BasicElement]:
        """
        <target0, target1, ...> = <value>;
        """
        # Check if contains function call
        for child in pyast.walk(node):
            if isinstance(child, pyast.Call):
                return self.__parse_assign_to_call(node, prefix)
        assign = ir.AssignNode(
            unique_id=prefix,
            lvalue=self.__parse_targets(node.targets),
            rvalue=self.__parse_expression(node.value),
        )
        return (assign, assign)

    def __parse_statements(
        self, stmts: list[pyast.stmt], prefix: str, nextt: ir.Element
    ):
        """
        Returns state of the first stmt in block

        Give it a prefix and name-mangling is handled for you

        {
            <statement0>
            <statement1>
            ...
        }
        """
        assert isinstance(stmts, list)
        assert isinstance(prefix, str)

        # builds backwards
        stmts.reverse()
        previous = self.__parse_statement(
            stmt=stmts[0], nextt=nextt, prefix=f"{prefix}_0"
        )
        for i in range(1, len(stmts)):
            previous = self.__parse_statement(
                stmt=stmts[i], nextt=previous, prefix=f"{prefix}_{i}"
            )
        return previous

    def __parse_statement(self, stmt: pyast.AST, nextt: ir.Element, prefix: str):
        """
        nextt represents the next operation in the control flow diagram.

        e.g. what does the program do after this current stmt (if-else/assignment)?

        returns the node that has been created

        <statement> (e.g. assign, for loop, etc., cannot be equated to)

        """
        get_typed(stmt, pyast.AST)
        get_typed(nextt, ir.Element)
        if isinstance(stmt, pyast.Assign):
            cur_node, end_node = self.__parse_assign(stmt, prefix=prefix)
            edge = ir.ClockedEdge(unique_id=f"{prefix}_e", child=nextt)
            end_node.child = edge
        elif isinstance(stmt, pyast.Yield):
            cur_node = self.__parse_yield(stmt, prefix=prefix)
            edge = ir.ClockedEdge(unique_id=f"{prefix}_e", child=nextt)
            cur_node.child = edge
        elif isinstance(stmt, pyast.While):
            cur_node = self.__parse_while(stmt, nextt=nextt, prefix=prefix)
        elif isinstance(stmt, pyast.For):
            cur_node = self.__parse_for(stmt, nextt=nextt, prefix=prefix)
        elif isinstance(stmt, pyast.If):
            cur_node = self.__parse_ifelse(stmt=stmt, nextt=nextt, prefix=prefix)
        elif isinstance(stmt, pyast.Expr):
            cur_node = self.__parse_statement(
                stmt=stmt.value, nextt=nextt, prefix=prefix
            )
        elif isinstance(stmt, pyast.AugAssign):
            assert isinstance(
                stmt.target, pyast.Name
            ), "Error: only supports single target"
            edge = ir.ClockedEdge(unique_id=f"{prefix}_e", child=nextt)
            cur_node = ir.AssignNode(
                unique_id=prefix,
                lvalue=self.__parse_expression(stmt.target),
                rvalue=self.__parse_expression(
                    pyast.BinOp(stmt.target, stmt.op, stmt.value)
                ),
                child=edge,
            )
        else:
            raise TypeError(
                "Error: unexpected statement type", type(stmt), pyast.dump(stmt)
            )
        return cur_node

    def __parse_for(self, stmt: pyast.For, nextt: ir.Element, prefix: str):
        """
        For ... in ...:
        """
        loop_edge = ir.ClockedEdge(unique_id=f"{prefix}_edge", name="True")
        done_edge = ir.ClockedEdge(unique_id=f"{prefix}_f", name="False", child=nextt)

        target = stmt.iter
        assert isinstance(target, pyast.Name)
        if target.id not in self._context.instances:
            raise RuntimeError(f"No iterator instance {self._context.instances}")
        instance = self._context.instances[target.id]

        def unique_node_gen():
            counter = 0
            while True:
                yield f"{prefix}_call_{counter}"

        def unique_edge_gen():
            counter = 0
            while True:
                yield f"{prefix}_call_{counter}_e"

        unique_node = unique_node_gen()
        unique_edge = unique_edge_gen()

        head = ir.AssignNode(
            unique_id=next(unique_node),
            lvalue=instance.ready_signal,
            rvalue=ir.UInt(1),
        )
        node: ir.BasicElement = head
        node.child = ir.NonClockedEdge(unique_id=next(unique_edge))
        node = node.child
        node.child = ir.AssignNode(
            unique_id=next(unique_node),
            lvalue=instance.start_signal,
            rvalue=ir.UInt(0),
        )
        node = node.child
        node.child = ir.NonClockedEdge(unique_id=next(unique_edge))
        node = node.child

        edge_to_head = ir.ClockedEdge(unique_id=next(unique_edge), child=head)
        second_ifelse0 = ir.IfElseNode(
            unique_id=f"{prefix}_for_done_0",
            condition=instance.done_signal,
            true_edge=done_edge,
            false_edge=loop_edge,
        )
        edge_to_second_ifelse0 = ir.NonClockedEdge(
            unique_id=next(unique_edge), child=second_ifelse0
        )
        second_ifelse1 = ir.IfElseNode(
            unique_id=f"{prefix}_for_done_1",
            condition=instance.done_signal,
            true_edge=done_edge,
            false_edge=edge_to_head,
        )

        # capture output
        if not isinstance(stmt.target, pyast.Tuple):
            assert isinstance(stmt.target, pyast.Name)
            outputs = [ir.Var(stmt.target.id)]
        else:
            outputs = list(map(name_to_var, stmt.target.elts))
        assert len(outputs) == len(instance.outputs)
        capture_head = ir.AssignNode(
            unique_id=next(unique_node), lvalue=instance.ready_signal, rvalue=ir.UInt(0)
        )
        capture_node: ir.BasicElement = capture_head
        for caller, callee in zip(outputs, instance.outputs):
            capture_node.child = ir.NonClockedEdge(unique_id=next(unique_edge))
            capture_node = capture_node.child
            capture_node.child = ir.AssignNode(
                unique_id=next(unique_node), lvalue=caller, rvalue=callee
            )
            capture_node = capture_node.child
            if not self._context.is_declared(str(caller)):
                self._context.add_global_var(caller)

        capture_node.child = edge_to_second_ifelse0
        capture_node = capture_head

        edge_to_second_ifelse1 = ir.NonClockedEdge(
            unique_id=next(unique_edge), child=second_ifelse1
        )
        edge_to_capture_head = ir.NonClockedEdge(
            unique_id=next(unique_edge), child=capture_head
        )
        first_ifelse = ir.IfElseNode(
            unique_id=f"{prefix}_for_loop",
            condition=ir.UBinOp(instance.ready_signal, "&&", instance.valid_signal),
            true_edge=edge_to_capture_head,  # replaced with linked list for output
            false_edge=edge_to_second_ifelse1,
        )
        node.child = first_ifelse

        body_node = self.__parse_statements(stmt.body, f"{prefix}_for", head)
        loop_edge.child = body_node

        return head

    def __parse_ifelse(self, stmt: pyast.If, nextt: ir.Element, prefix: str):
        """
        If else block
        """
        assert isinstance(stmt, pyast.If)

        then_node = self.__parse_statements(stmt.body, f"{prefix}_t", nextt)
        to_then = ir.ClockedEdge(
            unique_id=f"{prefix}_true_edge", name="True", child=then_node
        )
        if stmt.orelse:
            else_node = self.__parse_statements(stmt.orelse, f"{prefix}_f", nextt)
            to_else = ir.ClockedEdge(
                unique_id=f"{prefix}_false_edge", name="False", child=else_node
            )
            ifelse = ir.IfElseNode(
                unique_id=prefix,
                true_edge=to_then,
                false_edge=to_else,
                condition=self.__parse_expression(stmt.test),
            )
        else:
            to_else = ir.ClockedEdge(
                unique_id=f"{prefix}_false_edge", name="False", child=nextt
            )
            ifelse = ir.IfElseNode(
                unique_id=prefix,
                true_edge=to_then,
                false_edge=to_else,
                condition=self.__parse_expression(stmt.test),
            )

        return ifelse

    def __parse_while(self, stmt: pyast.While, nextt: ir.Element, prefix: str):
        """
        Converts while loop to a while-true-if-break loop
        """
        assert isinstance(stmt, pyast.While)

        loop_edge = ir.ClockedEdge(unique_id=f"{prefix}_edge", name="True")
        done_edge = ir.ClockedEdge(unique_id=f"{prefix}_f", name="False", child=nextt)

        ifelse = ir.IfElseNode(
            unique_id=f"{prefix}_while",
            condition=self.__parse_expression(stmt.test),
            true_edge=loop_edge,
            false_edge=done_edge,
        )
        body_node = self.__parse_statements(stmt.body, f"{prefix}_while", ifelse)
        loop_edge.child = body_node

        return ifelse

    def __parse_yield(self, node: pyast.Yield, prefix: str):
        """
        yield <value>;
        """
        if isinstance(node.value, pyast.Tuple):
            return ir.YieldNode(
                unique_id=prefix,
                name="Yield",
                stmts=[self.__parse_expression(c) for c in node.value.elts],
            )
        if isinstance(
            node.value, (pyast.Name, pyast.BinOp, pyast.Compare, pyast.UnaryOp)
        ):
            return ir.YieldNode(
                unique_id=prefix,
                name="Yield",
                stmts=[self.__parse_expression(c) for c in [node.value]],
            )
        raise TypeError(f"Expected tuple {type(node.value)}")

    def __parse_binop(self, expr: pyast.BinOp) -> ir.Expression:
        """
        <left> <op> <right>

        With special case for floor division
        """
        if isinstance(expr.op, pyast.Add):
            return ir.Add(
                self.__parse_expression(expr.left), self.__parse_expression(expr.right)
            )
        if isinstance(expr.op, pyast.Sub):
            return ir.Sub(
                self.__parse_expression(expr.left), self.__parse_expression(expr.right)
            )

        if isinstance(expr.op, pyast.Mult):
            return ir.Mul(
                self.__parse_expression(expr.left), self.__parse_expression(expr.right)
            )

        if isinstance(expr.op, pyast.FloorDiv):
            var_a = self.__parse_expression(expr.left)
            var_b = self.__parse_expression(expr.right)
            return ir.Ternary(
                condition=ir.BinOp(
                    left=ir.BinOp(left=var_a, right=var_b, oper="%"),
                    right=ir.Int(0),
                    oper="===",
                ),
                left=ir.BinOp(var_a, "/", var_b),
                right=ir.BinOp(
                    ir.BinOp(var_a, "/", var_b),
                    "-",
                    ir.BinOp(
                        ir.UBinOp(
                            ir.BinOp(var_a, "<", ir.Int(0)),
                            "^",
                            ir.BinOp(var_b, "<", ir.Int(0)),
                        ),
                        "&",
                        ir.Int(1),
                    ),
                ),
            )
        if isinstance(expr.op, pyast.Mod):
            var_a = self.__parse_expression(expr.left)
            var_b = self.__parse_expression(expr.right)
            return ir.Ternary(
                ir.UBinOp(var_a, "<", ir.Int(0)),
                ir.Ternary(
                    ir.UBinOp(var_b, ">=", ir.Int(0)),
                    ir.UnaryOp("-", ir.Mod(var_a, var_b)),
                    ir.Mod(var_a, var_b),
                ),
                ir.Ternary(
                    ir.UBinOp(var_b, "<", ir.Int(0)),
                    ir.UnaryOp("-", ir.Mod(var_a, var_b)),
                    ir.Mod(var_a, var_b),
                ),
            )
        raise TypeError(
            "Error: unexpected binop type", type(expr.op), pyast.dump(expr.op)
        )

    def __parse_expression(self, expr: pyast.AST) -> ir.Expression:
        """
        <expression> (e.g. constant, name, subscript, etc., those that return a value)
        """
        if isinstance(expr, pyast.Constant):
            return ir.Int(expr.value)
        if isinstance(expr, pyast.Name):
            return ir.Var(py_name=expr.id)
        if isinstance(expr, pyast.Subscript):
            return self.__parse_subscript(expr)
        if isinstance(expr, pyast.BinOp):
            return self.__parse_binop(expr)
        if isinstance(expr, pyast.UnaryOp):
            if isinstance(expr.op, pyast.USub):
                return ir.UnaryOp("-", self.__parse_expression(expr.operand))
            raise TypeError(
                "Error: unexpected unaryop type", type(expr.op), pyast.dump(expr.op)
            )
        if isinstance(expr, pyast.Compare):
            return self.__parse_compare(expr)
        if isinstance(expr, pyast.BoolOp):
            if isinstance(expr.op, pyast.And):
                return ir.Expression(
                    f"({self.__parse_expression(expr.values[0]).to_string()}) \
                    && ({self.__parse_expression(expr.values[1]).to_string()})"
                )
        # if isinstance(expr, pyast.Call):
        #     return self.__parse_call(expr)
        raise TypeError(
            "Error: unexpected expression type", type(expr), pyast.dump(expr)
        )

    def __parse_assign_to_call(
        self, assign: pyast.Assign, prefix: str
    ) -> tuple[ir.BasicElement, ir.BasicElement]:
        """
        instance = func(args, ...)
        """
        # print(pyast.dump(assign))
        assert len(assign.targets) == 1
        target = assign.targets[0]
        assert isinstance(target, pyast.Name)
        instance = self._context.instances[target.id]

        def unique_node_gen():
            counter = 0
            while True:
                yield f"{prefix}_call_{counter}"

        def unique_edge_gen():
            counter = 0
            while True:
                yield f"{prefix}_call_{counter}_e"

        unique_node = unique_node_gen()
        unique_edge = unique_edge_gen()

        head = ir.AssignNode(
            unique_id=next(unique_node),
            lvalue=instance.ready_signal,
            rvalue=ir.UInt(0),
        )
        node: ir.BasicElement = head
        node.child = ir.NonClockedEdge(unique_id=next(unique_edge))
        node = node.child
        node.child = ir.AssignNode(
            unique_id=next(unique_node),
            lvalue=instance.start_signal,
            rvalue=ir.UInt(1),
        )
        node = node.child

        assert isinstance(assign.value, pyast.Call)

        arguments = list(map(name_to_var, assign.value.args))
        assert len(arguments) == len(instance.inputs)

        for arg, param in zip(arguments, instance.inputs):
            node.child = ir.NonClockedEdge(unique_id=next(unique_edge))
            node = node.child
            node.child = ir.AssignNode(
                unique_id=next(unique_node),
                lvalue=param,
                rvalue=arg,
            )
            node = node.child

        return (head, node)

    def __parse_subscript(self, node: pyast.Subscript) -> ir.Expression:
        """
        <value>[<slice>]
        Note: built from right to left, e.g. [z] -> [y][z] -> [x][y][z] -> matrix[x][y][z]
        """
        return ir.Expression(
            f"{self.__parse_expression(node.value).to_string()}\
                [{self.__parse_expression(node.slice).to_string()}]"
        )

    def __parse_compare(self, node: pyast.Compare) -> ir.UBinOp:
        """
        <left> <op> <comparators>
        """
        assert len(node.ops) == 1
        assert len(node.comparators) == 1

        if isinstance(node.ops[0], pyast.Lt):
            return ir.LessThan(
                self.__parse_expression(node.left),
                self.__parse_expression(node.comparators[0]),
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
            left=self.__parse_expression(node.left),
            oper=operator,
            right=self.__parse_expression(node.comparators[0]),
        )
