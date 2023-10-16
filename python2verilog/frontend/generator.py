"""
The freshest in-order generator parser
"""
import ast as pyast
import copy
import itertools
import logging
from typing import Collection, Iterable, Optional, TypeVar, cast

from typing_extensions import TypeAlias

from python2verilog import ir
from python2verilog.exceptions import UnsupportedSyntaxError
from python2verilog.utils.typed import guard, typed_list, typed_strict


class GeneratorFunc:
    """
    In-order generator function parser
    """

    ParseResult: TypeAlias = tuple[ir.Node, list[ir.Edge]]

    def __init__(self, context: ir.Context) -> None:
        self._context = copy.deepcopy(context)

    def create_root(self) -> tuple[ir.Node, ir.Context]:
        """
        Returns the root node and context
        """
        return self._parse_func(), self._context

    def _create_done(self, prefix: str) -> ir.Node:
        """
        Creates the done nodes

        Signals that module is done, happens in one clock cycle

        Current implementation is as follows:

        done = 1
        valid = 1
        """
        left_hand_sides = [
            self._context.signals.done,
            self._context.signals.valid,
            self._context.state_var,
        ]
        right_hand_sides = [ir.UInt(1), ir.UInt(1), self._context.idle_state]
        head, _tail = self._weave_nonclocked_edges(
            self._create_assign_nodes(left_hand_sides, right_hand_sides, prefix=prefix),
            prefix=f"{prefix}_e",
            last_edge=False,
        )
        return head

    def _parse_func(self, prefix: str = "_state") -> ir.Node:
        """
        Parses the function inside the context
        """
        breaks: list[ir.Edge] = []
        continues: list[ir.Edge] = []
        body_head, prev_tails = self._parse_stmts(
            self._context.py_ast.body, prefix=prefix, breaks=breaks, continues=continues
        )
        assert len(breaks) == 0
        assert len(continues) == 0
        for tail in prev_tails:
            tail.child = self._create_done(prefix="_state_done")
        self._context.entry_state = ir.State(body_head.unique_id)

        return body_head

    def _parse_stmt(
        self,
        stmt: pyast.AST,
        breaks: list[ir.Edge],
        continues: list[ir.Edge],
        prefix: str,
    ) -> ParseResult:
        """
        Parses a statement

        :param stmt: statement to-be-parsed
        :param breaks: list of edges that connect to end of break stmt
        :param continues: where to connect continue edges
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
            assert guard(nothing.child, ir.Edge)
            breaks.append(nothing.child)
            return nothing, []
        if isinstance(stmt, pyast.If):
            return self._parse_ifelse(
                ifelse=stmt, prefix=prefix, breaks=breaks, continues=continues
            )
        if isinstance(stmt, pyast.For):
            return self._parse_for(stmt=stmt, prefix=prefix)
        if isinstance(stmt, pyast.AugAssign):
            assert isinstance(
                stmt.target, pyast.Name
            ), "Error: only supports single target"
            edge = ir.ClockedEdge(unique_id=f"{prefix}_e")
            lvalue = self._parse_expression(stmt.target)
            assert guard(lvalue, ir.Var)
            cur_node = ir.AssignNode(
                unique_id=prefix,
                lvalue=lvalue,
                rvalue=self._parse_expression(
                    pyast.BinOp(stmt.target, stmt.op, stmt.value)
                ),
                child=edge,
            )
            return cur_node, [edge]
        if isinstance(stmt, pyast.Constant):
            # Probably a triple-quote comment
            assert guard(stmt.value, str)
            dummy = ir.AssignNode(
                unique_id=prefix,
                name="dummy",
                lvalue=self._context.state_var,
                rvalue=self._context.state_var,
                child=ir.ClockedEdge(
                    unique_id=f"{prefix}_e",
                ),
            )
            assert guard(dummy.child, ir.Edge)
            return dummy, [dummy.child]
        if isinstance(stmt, pyast.Continue):
            nothing = ir.AssignNode(
                unique_id=prefix,
                name="break",
                lvalue=self._context.state_var,
                rvalue=self._context.state_var,
                child=ir.ClockedEdge(
                    unique_id=f"{prefix}_e",
                ),
            )
            assert guard(nothing.child, ir.Edge)
            continues.append(nothing.child)
            return nothing, []
        if isinstance(stmt, pyast.Return):
            if stmt.value is not None:
                raise UnsupportedSyntaxError.from_pyast(stmt)
            done = self._create_done(prefix=prefix)
            return done, []

        raise TypeError(f"Unexpected statement {pyast.dump(stmt)}")

    def _parse_stmts(
        self,
        stmts: list[pyast.stmt],
        prefix: str,
        breaks: list[ir.Edge],
        continues: list[ir.Edge],
    ) -> ParseResult:
        """
        A helper for parsing statements (blocks of code)

        :return: (head, breaks, continues, ends)
        - head is the head of this body (first node in body)
        - ends are edges come from end of body (what to do after body)
        """
        body_head: Optional[ir.Node] = None
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
            if prev_tails is not None:
                for tail in prev_tails:
                    tail.child = head_node
            prev_tails = typed_list(tail_edges, ir.Edge)
            assert guard(head_node, ir.Node)

        assert prev_tails is not None
        assert body_head is not None
        return body_head, prev_tails

    def _parse_assign_to_call(self, assign: pyast.Assign, prefix: str) -> ParseResult:
        """
        instance = func(args, ...)
        """
        assert isinstance(assign.value, pyast.Call)
        assert len(assign.targets) == 1
        target = assign.targets[0]
        assert isinstance(target, pyast.Name)

        def create_instance(caller_cxt: ir.Context):
            # Figure out target name
            target_name = target.id

            # Figure out func being called
            assert guard(assign.value, pyast.Call)
            func = assign.value.func
            assert guard(func, pyast.Name)
            func_name = func.id

            # Get context of generator function being called
            callee_cxt = caller_cxt.namespace[func_name]

            # Create an instance of that generator
            instance = callee_cxt.create_instance(target_name)

            # Add instance to own context
            caller_cxt.instances[target_name] = instance

        create_instance(self._context)
        inst = self._context.instances[target.id]

        def unique_node_gen():
            counter = 0
            while True:
                yield f"{prefix}_call_{counter}"
                counter += 1

        def unique_edge_gen():
            counter = 0
            while True:
                yield f"{prefix}_call_{counter}_e"
                counter += 1

        unique_node = unique_node_gen()
        unique_edge = unique_edge_gen()

        # Nessessary for exclusivity
        head = ir.AssignNode(
            unique_id=next(unique_node),
            lvalue=inst.signals.ready,
            rvalue=ir.UInt(0),
        )

        node: ir.BasicElement = head

        node.child = ir.NonClockedEdge(
            unique_id=next(unique_edge),
        )
        node = node.child

        node.child = ir.AssignNode(
            unique_id=next(unique_node),
            lvalue=inst.signals.start,
            rvalue=ir.UInt(1),
        )
        node = node.child
        node.child = ir.NonClockedEdge(
            unique_id=next(unique_edge),
        )
        node = node.child

        assert isinstance(assign.value, pyast.Call)

        arguments = list(map(self._parse_expression, assign.value.args))

        assert len(arguments) == len(inst.inputs)

        assign_head, tail = self._weave_nonclocked_edges(
            self._create_assign_nodes(inst.inputs, arguments, prefix),
            f"{prefix}_e",
        )
        node.child = assign_head
        tail.child = ir.ClockedEdge(
            unique_id=next(unique_edge),
        )
        return head, [tail.child]

    @staticmethod
    def _name_to_var(name: pyast.expr) -> ir.Var:
        """
        Converts a pyast.Name to a ir.Var using its id
        """
        assert isinstance(name, pyast.Name)
        return ir.Var(name.id)

    def _parse_for(self, stmt: pyast.For, prefix: str) -> ParseResult:
        """
        For ... in ...:
        """
        # pylint: disable=too-many-locals
        breaks: list[ir.Edge] = []
        continues: list[ir.Edge] = []
        assert not stmt.orelse, "for-else statements not supported"
        target = stmt.iter
        assert isinstance(target, pyast.Name)
        if target.id not in self._context.instances:
            raise RuntimeError(f"No iterator instance {self._context.instances}")
        inst = self._context.instances[target.id]

        def gen_unique_node():
            counter = 0
            while True:
                yield f"{prefix}_for_{counter}"
                counter += 1

        def gen_unique_edge():
            counter = 0
            while True:
                yield f"{prefix}_for_{counter}_e"
                counter += 1

        unique_node = gen_unique_node()
        unique_edge = gen_unique_edge()

        to_done = ir.ClockedEdge(next(unique_edge))  # goto end of for
        to_body = ir.ClockedEdge(next(unique_edge))  # goto body of for
        to_wait = ir.ClockedEdge(next(unique_edge))  # repeat check

        to_inner = ir.NonClockedEdge(
            next(unique_edge)
        )  # to inner ifelse (done or iterate)

        head = ir.IfElseNode(
            unique_id=next(unique_node),
            condition=ir.UBinOp(inst.signals.ready, "&&", inst.signals.valid),
            true_edge=to_inner,
            false_edge=to_wait,
        )

        # repeat check
        to_wait.child = ir.IfElseNode(
            unique_id=next(unique_node),
            condition=ir.UBinOp(
                self._context.signals.ready,
                "||",
                ir.UnaryOp("!", self._context.signals.valid),
            ),
            true_edge=ir.NonClockedEdge(
                next(unique_edge),
                child=ir.AssignNode(
                    unique_id=next(unique_node),
                    lvalue=inst.signals.ready,
                    rvalue=ir.UInt(1),
                    child=ir.ClockedEdge(next(unique_edge), child=head),
                ),
            ),
            false_edge=ir.ClockedEdge(next(unique_edge), child=head),
        )

        # inner ifelse
        to_capture = ir.NonClockedEdge(next(unique_edge))
        to_inner.child = ir.AssignNode(
            unique_id=next(unique_node),
            lvalue=inst.signals.ready,
            rvalue=ir.UInt(0),
            child=ir.NonClockedEdge(
                next(unique_edge),
                child=ir.IfElseNode(
                    unique_id=next(unique_node),
                    condition=inst.signals.done,
                    true_edge=to_done,
                    false_edge=to_capture,
                ),
            ),
        )

        def create_capture_output_nodes():
            if not isinstance(stmt.target, pyast.Tuple):
                assert isinstance(stmt.target, pyast.Name)
                outputs = [ir.Var(stmt.target.id)]
            else:
                outputs = list(map(self._name_to_var, stmt.target.elts))
            assert len(outputs) == len(inst.outputs), f"{outputs} {inst.outputs}"

            dummy = ir.NonClockedEdge(next(unique_edge))
            prev_edge: ir.Edge = dummy
            for caller, callee in zip(outputs, inst.outputs):
                assert guard(prev_edge, ir.Edge)
                prev_assign = ir.AssignNode(
                    unique_id=next(unique_node),
                    lvalue=caller,
                    rvalue=callee,
                    child=ir.NonClockedEdge(next(unique_edge)),
                )
                prev_edge.child = prev_assign
                assert guard(prev_assign.child, ir.Edge)
                prev_edge = prev_assign.child
                if not self._context.is_declared(caller.ver_name):
                    self._context.add_global_var(caller)

            assert guard(prev_assign, ir.AssignNode)
            prev_assign.child = to_body
            return dummy.child

        capture_node = create_capture_output_nodes()
        assert guard(capture_node, ir.AssignNode)
        to_capture.child = capture_node

        body_node, ends = self._parse_stmts(
            stmts=stmt.body,
            prefix=f"{prefix}_for_body",
            breaks=breaks,
            continues=continues,
        )
        to_body.child = body_node

        for cont in continues:
            cont.child = head
        for end in ends:
            end.child = head

        return head, [to_done, *breaks]

    def _parse_while(self, whil: pyast.While, prefix: str) -> ParseResult:
        assert not whil.orelse, "while-else statements not supported"
        breaks: list[ir.Edge] = []
        continues: list[ir.Edge] = []
        body_head, ends = self._parse_stmts(
            stmts=whil.body,
            prefix=f"{prefix}_while",
            breaks=breaks,
            continues=continues,
        )
        done_edge = ir.ClockedEdge(unique_id=f"{prefix}_done_e")
        while_head = ir.IfElseNode(
            unique_id=f"{prefix}_while",
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
    ) -> ParseResult:
        then_head, then_ends = self._parse_stmts(
            stmts=ifelse.body,
            prefix=f"{prefix}_then",
            breaks=breaks,
            continues=continues,
        )
        to_then = ir.NonClockedEdge(unique_id=f"{prefix}_then_e", child=then_head)

        if ifelse.orelse:
            else_head, else_ends = self._parse_stmts(
                stmts=ifelse.orelse,
                prefix=f"{prefix}_else",
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

        # No else
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

    def _parse_yield(self, yiel: pyast.Yield, prefix: str) -> ParseResult:
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

        self._context.validate()
        head, tail = self._weave_nonclocked_edges(
            self._create_assign_nodes(self._context.output_vars, stmts, prefix),
            f"{prefix}_e",
        )
        tail_edge: ir.Edge = tail.edge  # get last nonclocked edge
        tail_edge.child = ir.AssignNode(
            unique_id=f"{prefix}_valid",
            lvalue=self._context.signals.valid,
            rvalue=ir.UInt(1),
            child=ir.ClockedEdge(unique_id=f"{prefix}_e"),
        )
        return head, [tail_edge.child.edge]

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
        variables: Collection[ir.Var],
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

    _BasicNodeType = TypeVar("_BasicNodeType", bound=ir.BasicNode)

    @staticmethod
    def _weave_nonclocked_edges(
        nodes: Iterable[_BasicNodeType], prefix: str, last_edge: bool = True
    ) -> tuple[_BasicNodeType, _BasicNodeType]:
        """
        Weaves nodes with nonclocked edges.

        :param last_edge: if True, include last nonclocked edge
        :return: (first basic node, last basic node)
        """
        counters = itertools.count()
        head: Optional[ir.BasicNode] = None
        prev: Optional[ir.BasicElement] = None
        node: ir.BasicElement = ir.BasicElement(unique_id="DUMMY")
        for node, counter in zip(nodes, counters):
            if not head:
                head = node
            if prev:
                prev.child = node
            node.child = ir.NonClockedEdge(
                unique_id=f"{prefix}_{counter}",
            )
            prev = node.child
        if not last_edge:
            node._child = None  # pylint: disable=protected-access
        return cast(GeneratorFunc._BasicNodeType, head), node

    def _parse_assign(self, assign: pyast.Assign, prefix: str) -> ParseResult:
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
        if isinstance(assign.value, pyast.Call):
            return self._parse_assign_to_call(assign=assign, prefix=prefix)

        assert len(assign.targets) == 1
        targets, values = zip(
            *self._target_value_visitor(assign.targets[0], assign.value)
        )

        head, tail = self._weave_nonclocked_edges(
            self._create_assign_nodes(targets, values, prefix),
            f"{prefix}_e",
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
        try:
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
            if isinstance(expr, pyast.Compare):
                return self._parse_compare(expr)
            if isinstance(expr, pyast.BoolOp):
                if isinstance(expr.op, pyast.And):
                    return ir.UBinOp(
                        self._parse_expression(expr.values[0]),
                        "&&",
                        self._parse_expression(expr.values[1]),
                    )
        except Exception as e:
            raise UnsupportedSyntaxError.from_pyast(expr) from e
        raise UnsupportedSyntaxError.from_pyast(expr)

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
            raise UnsupportedSyntaxError(f"Unknown operator {pyast.dump(node.ops[0])}")
        return ir.UBinOp(
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
        raise UnsupportedSyntaxError(f"Unexpected binop type {pyast.dump(expr.op)}")
