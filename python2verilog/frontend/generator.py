"""
Parses Python Generator Functions to Intermediate Representation
"""

from __future__ import annotations

import ast as pyast
import itertools
import logging
from typing import Collection, Iterable, Literal, Optional, overload

from python2verilog import ir
from python2verilog.utils.lines import Indent, Lines
from python2verilog.utils.typed import guard, typed, typed_list, typed_strict


class FromGenerator:
    """
    Parses python generator functions to Verilog AST
    """

    def __init__(
        self,
        context: ir.Context,
    ):
        """
        Initializes the parser, does quick setup work
        """
        self._context = typed_strict(context, ir.Context)

    @staticmethod
    def _create_instances(caller_cxt: ir.Context):
        """
        Add generator instances of all functions called by caller

        e.g. target_name = func_name(...)
        """
        for node in caller_cxt.py_ast.body:
            for child in pyast.walk(node):
                if isinstance(child, pyast.Assign) and isinstance(
                    child.value, pyast.Call
                ):
                    # Figure out target name
                    assert len(child.targets) == 1
                    target = child.targets[0]
                    assert guard(target, pyast.Name)
                    target_name = target.id

                    # Figure out func being called
                    func = child.value.func
                    assert guard(func, pyast.Name)
                    func_name = func.id

                    # Get context of generator function being called
                    callee_cxt = caller_cxt.namespace[func_name]

                    # Create an instance of that generator
                    instance = callee_cxt.create_instance(target_name)

                    # Add instance to own context
                    caller_cxt.instances[target_name] = instance

                # Python 3.10+
                # match child:
                #     case pyast.Assign(
                #         targets=[pyast.Name(id=target_name)],
                #         value=pyast.Call(func=pyast.Name(id=func_name)),
                #     ):
                #         # Get context of generator function being called
                #         callee_cxt = caller_cxt.namespace[func_name]

                #         # Create an instance of that generator
                #         instance = callee_cxt.create_instance(target_name)

                #         # Add instance to own context
                #         caller_cxt.instances[target_name] = instance

    @staticmethod
    def _name_to_var(name: pyast.expr) -> ir.Var:
        """
        Converts a pyast.Name to a ir.Var using its id
        """
        assert isinstance(name, pyast.Name)
        return ir.Var(name.id)

    def create_root(self):
        """
        Returns tuple containing the root and the context
        """
        self._context.validate()
        self._create_instances(self._context)

        logging.debug("\n\n========> Parsing %s <========", self._context.name)
        root = self.__parse_statements(
            stmts=self._context.py_ast.body,
            prefix="_state",
            nextt=ir.DoneNode(unique_id=str(self._context.done_state), name="done"),
        )

        self._context.entry_state = ir.State(root.unique_id)
        logging.debug("Entry state is %s", self._context.entry_state)
        return (root, self._context)

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
            yield (ir.Var(target.id), self.__parse_expression(value))
        else:
            raise TypeError(f"{pyast.dump(target)} {pyast.dump(value)}")

    def __parse_assign(
        self, node: pyast.Assign, prefix: str
    ) -> tuple[ir.BasicElement, ir.BasicElement]:
        """
        <target0, target1, ...> = <value>;
        """
        # Check if value is a function call
        if isinstance(node.value, pyast.Call):
            return self.__parse_assign_to_call(node, prefix)

        assert len(node.targets) == 1
        targets, values = zip(*self._target_value_visitor(node.targets[0], node.value))

        # pylint: disable=unpacking-non-sequence
        head, tail = self._weave_nonclocked_edges(
            self._create_assign_nodes(targets, values, prefix),
            f"{prefix}_e",
            last_edge=False,
        )
        logging.debug("Assign Head %s", list(head.visit_nonclocked()))

        return head, tail

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
        previous = self.__parse(stmt=stmts[0], nextt=nextt, prefix=f"{prefix}_0")
        for i in range(1, len(stmts)):
            previous = self.__parse(
                stmt=stmts[i], nextt=previous, prefix=f"{prefix}_{i}"
            )
        return previous

    def __parse(self, stmt: pyast.AST, nextt: ir.Element, prefix: str):
        """
        nextt represents the next operation in the control flow diagram.

        e.g. what does the program do after this current stmt (if-else/assignment)?

        returns the node that has been created

        <statement> (e.g. assign, for loop, etc., cannot be equated to)

        """
        typed(stmt, pyast.AST)
        typed(nextt, ir.Element)
        if isinstance(stmt, pyast.Assign):
            cur_node, end_node = self.__parse_assign(stmt, prefix=prefix)
            edge = ir.ClockedEdge(unique_id=f"{prefix}_e", child=nextt)
            end_node.child = edge
            logging.debug(
                "Assign %s %s => %s => %s",
                cur_node.unique_id,
                cur_node,
                end_node,
                nextt.unique_id,
            )
        elif isinstance(stmt, pyast.Yield):
            cur_node, end_node = self.__parse_yield(stmt, prefix=prefix)
            edge = ir.ClockedEdge(unique_id=f"{prefix}_e", child=nextt)
            end_node.child = edge
        elif isinstance(stmt, pyast.While):
            cur_node = self.__parse_while(stmt, nextt=nextt, prefix=prefix)
        elif isinstance(stmt, pyast.For):
            cur_node = self.__parse_for(stmt, nextt=nextt, prefix=prefix)
            logging.debug(
                "For %s %s => %s", cur_node.unique_id, cur_node, nextt.unique_id
            )
        elif isinstance(stmt, pyast.If):
            cur_node = self.__parse_ifelse(stmt=stmt, nextt=nextt, prefix=prefix)
        elif isinstance(stmt, pyast.Expr):
            cur_node = self.__parse(stmt=stmt.value, nextt=nextt, prefix=prefix)
        elif isinstance(stmt, pyast.AugAssign):
            assert isinstance(
                stmt.target, pyast.Name
            ), "Error: only supports single target"
            edge = ir.ClockedEdge(unique_id=f"{prefix}_e", child=nextt)
            lvalue = self.__parse_expression(stmt.target)
            assert guard(lvalue, ir.Var)
            cur_node = ir.AssignNode(
                unique_id=prefix,
                lvalue=lvalue,
                rvalue=self.__parse_expression(
                    pyast.BinOp(stmt.target, stmt.op, stmt.value)
                ),
                child=edge,
            )
        elif isinstance(stmt, pyast.Constant):
            assert "\n" in stmt.value, f"Error: parsing {pyast.dump(stmt)}"
            logging.debug("Parsing triple-quote comment %s", stmt.value)
            # Fix for triple-quote comments in code
            edge = ir.ClockedEdge(unique_id=f"{prefix}_e", child=nextt)
            cur_node = ir.AssignNode(
                unique_id=prefix,
                lvalue=self._context.state_var,
                rvalue=self._context.state_var,
                child=edge,
            )
        else:
            raise TypeError(
                f"Error: unexpected statement type {type(stmt)} {pyast.dump(stmt)}"
            )
        return cur_node

    def __parse_for(self, stmt: pyast.For, nextt: ir.Element, prefix: str):
        """
        For ... in ...:
        """
        # pylint: disable=too-many-locals
        loop_edge = ir.ClockedEdge(unique_id=f"{prefix}_edge", name="True")
        done_edge = ir.ClockedEdge(unique_id=f"{prefix}_f", name="False", child=nextt)

        target = stmt.iter
        assert isinstance(target, pyast.Name)
        if target.id not in self._context.instances:
            raise RuntimeError(f"No iterator instance {self._context.instances}")
        inst = self._context.instances[target.id]

        def unique_node_gen():
            counter = 0
            while True:
                yield f"{prefix}_for_{counter}"
                counter += 1

        def unique_edge_gen():
            counter = 0
            while True:
                yield f"{prefix}_for_{counter}_e"
                counter += 1

        unique_node = unique_node_gen()
        unique_edge = unique_edge_gen()

        head = ir.AssignNode(
            unique_id=next(unique_node),
            lvalue=inst.signals.ready,
            rvalue=ir.UInt(1),
        )
        node: ir.BasicElement = head
        node.child = ir.NonClockedEdge(unique_id=next(unique_edge))
        node = node.child

        edge_to_head = ir.ClockedEdge(unique_id=next(unique_edge), child=head)
        second_ifelse0 = ir.IfElseNode(
            unique_id=next(unique_node),
            condition=inst.signals.done,
            true_edge=done_edge,
            false_edge=loop_edge,
        )
        edge_to_second_ifelse0 = ir.NonClockedEdge(
            unique_id=next(unique_edge), child=second_ifelse0
        )
        second_ifelse1 = ir.IfElseNode(
            unique_id=next(unique_node),
            condition=inst.signals.done,
            true_edge=done_edge,
            false_edge=edge_to_head,
        )

        # capture output
        if not isinstance(stmt.target, pyast.Tuple):
            assert isinstance(stmt.target, pyast.Name)
            outputs = [ir.Var(stmt.target.id)]
        else:
            outputs = list(map(self._name_to_var, stmt.target.elts))
        assert len(outputs) == len(inst.outputs), f"{outputs} {inst.outputs}"
        capture_head = ir.AssignNode(
            unique_id=next(unique_node),
            lvalue=inst.signals.ready,
            rvalue=ir.UInt(0),
        )
        capture_node: ir.BasicElement = capture_head
        for caller, callee in zip(outputs, inst.outputs):
            capture_node.child = ir.NonClockedEdge(unique_id=next(unique_edge))
            capture_node = capture_node.child
            capture_node.child = ir.AssignNode(
                unique_id=next(unique_node), lvalue=caller, rvalue=callee
            )
            capture_node = capture_node.child
            if not self._context.is_declared(caller.ver_name):
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
            unique_id=next(unique_node),
            condition=ir.UBinOp(inst.signals.ready, "&&", inst.signals.valid),
            true_edge=edge_to_capture_head,  # replaced with linked list for output
            false_edge=edge_to_second_ifelse1,
        )
        node.child = first_ifelse

        body_node = self.__parse_statements(stmt.body, f"{prefix}_for_body", head)
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
                unique_id=f"{prefix}_{counter}", lvalue=var, rvalue=expr
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

    def __parse_yield(self, node: pyast.Yield, prefix: str):
        """
        yield <value>;
        """
        if isinstance(node.value, pyast.Tuple):
            stmts = [self.__parse_expression(c) for c in node.value.elts]
        elif isinstance(node.value, pyast.expr):
            stmts = [self.__parse_expression(node.value)]
        else:
            raise TypeError(f"Expected tuple {type(node.value)} {pyast.dump(node)}")

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
        )
        return head, tail.child

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
            left = self.__parse_expression(expr.left)
            right = self.__parse_expression(expr.right)
            return ir.FloorDiv(left, right)
        if isinstance(expr.op, pyast.Mod):
            left = self.__parse_expression(expr.left)
            right = self.__parse_expression(expr.right)
            return ir.Mod(left, right)
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
                return ir.UBinOp(
                    self.__parse_expression(expr.values[0]),
                    "&&",
                    self.__parse_expression(expr.values[1]),
                )
        raise TypeError(
            "Error: unexpected expression type", type(expr), pyast.dump(expr)
        )

    def __parse_assign_to_call(
        self, assign: pyast.Assign, prefix: str
    ) -> tuple[ir.BasicElement, ir.BasicElement]:
        """
        instance = func(args, ...)
        """
        assert len(assign.targets) == 1
        target = assign.targets[0]
        assert isinstance(target, pyast.Name)
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

        assert isinstance(assign.value, pyast.Call)

        arguments = list(map(self.__parse_expression, assign.value.args))

        assert len(arguments) == len(inst.inputs)

        for arg, param in zip(arguments, inst.inputs):
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
