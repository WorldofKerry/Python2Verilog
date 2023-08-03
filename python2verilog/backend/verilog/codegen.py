"""
Verilog Codegen
"""

from .ast import *


class CodeGen:
    """
    Code Generator for Verilog
    """

    @staticmethod
    def __new_module(root: Statement, context: ir.Context):
        """
        Creates a module wrapper from the context

        Requires context for I/O and declarations
        """
        assert isinstance(root, Statement)
        assert isinstance(context, ir.Context)
        inputs = []
        for var in context.input_vars:
            inputs.append(var)
        outputs = []
        for i in range(len((context.output_vars))):
            outputs.append(f"_out{str(i)}")
        # TODO: make these extras optional
        always = PosedgeSyncAlways(
            Expression("_clock"),
            valid="_valid",
            body=[CodeGen.__get_start_ifelse(root, context.global_vars)],
        )
        body: list[Statement] = [
            Declaration(v, is_reg=True, is_signed=True) for v in context.global_vars
        ]
        body.append(always)
        return Module(name=context.name, inputs=inputs, outputs=outputs, body=body)

    def __init__(self):
        self._context = None
        self._module = None

    @classmethod
    def from_list_ir(cls, root: ir.Statement, context: ir.Context):
        """
        Builds tree from list IR
        """
        assert isinstance(root, ir.Statement), f"got {type(root)} instead"
        assert isinstance(context, ir.Context)
        inst = CodeGen()
        inst._context = context
        inst._module = CodeGen.__new_module(CodeGen.list_build_stmt(root), context)
        return inst

    @classmethod
    def from_graph_ir(cls, root: ir.Element, context: ir.Context):
        """ "
        Builds tree from Graph IR
        """
        assert_type(root, ir.Element)
        assert_type(context, ir.Context)
        inst = CodeGen()
        inst._context = context
        root_case = inst.graph_build(root, set())
        inst._context.global_vars["_state"] = str(len(root_case.case_items))
        inst._module = CodeGen.__new_module(root_case, context)
        return inst

    @classmethod
    def from_optimal_ir(cls, root: ir.Vertex, context: ir.Context):
        """ "
        Builds tree from Graph IR
        """
        assert_type(root, ir.Vertex)
        assert_type(context, ir.Context)
        inst = CodeGen()
        inst._context = context
        old_case = inst.graph_build(root, set())
        root_case = CaseBuilder(root).case
        counter = len(old_case.case_items) + 1
        for item in root_case.case_items:
            if item.condition.to_string() not in inst._context.global_vars:
                inst._context.global_vars[item.condition.to_string()] = counter
                counter += 1
        inst._context.global_vars["_state"] = str(len(old_case.case_items))
        inst._module = CodeGen.__new_module(root_case, inst._context)
        return inst

    @staticmethod
    def list_build_stmt(node: ir.Statement) -> Statement:
        """
        Builds the Verilog AST
        """
        assert isinstance(node, (ir.Statement, ir.CaseItem))
        if not node:
            return Statement("")
        if isinstance(node, ir.Case):
            return CodeGen.list_build_case(node)
        if isinstance(node, ir.IfElse):
            then_body = []
            for stmt in node.then_body:
                then_body.append(CodeGen.list_build_stmt(stmt))
            else_body = []
            for stmt in node.else_body:
                else_body.append(CodeGen.list_build_stmt(stmt))
            return IfElse(CodeGen.list_build_expr(node.condition), then_body, else_body)
        if isinstance(node, ir.Statement):
            return Statement(node.to_string().replace("\n", " "))
        raise NotImplementedError(f"Unexpected type {type(node)}")

    @staticmethod
    def list_build_expr(node: ir.Expression) -> Expression:
        """
        Handles expressions
        """
        assert isinstance(node, ir.Expression)
        return Expression(node.to_string())

    @staticmethod
    def list_build_case(node: ir.Case) -> Case:
        """
        Handles case statements
        """
        assert isinstance(node, ir.Case)
        case_items = []
        for item in node.case_items:
            case_items.append(CodeGen.list_build_case_item(item))
        return Case(CodeGen.list_build_expr(node.condition), case_items)

    @staticmethod
    def list_build_case_item(node: ir.CaseItem) -> CaseItem:
        """
        Handles case item
        """
        case_items = []
        for item in node.statements:
            case_items.append(CodeGen.list_build_stmt(item))
        return CaseItem(CodeGen.list_build_expr(node.condition), case_items)

    def graph_build(self, root: ir.Element, visited: set[str]):
        """
        Builds from graph
        """
        assert_type(root, ir.Element)
        root_case = Case(expression=Expression("_state"), case_items=[])
        self.graph_build_node(node=root, root_case=root_case, visited=visited)
        return root_case

    def graph_build_node(self, node: ir.Element, root_case: Case, visited: set[str]):
        """
        Builds from node
        """
        assert_type(node, ir.Element)
        assert isinstance(self._context, ir.Context)
        if node.unique_id in visited:
            return node.unique_id

        if isinstance(node, ir.AssignNode):
            if node.unique_id not in visited:
                visited.add(node.unique_id)
                next_state = self.graph_build_node(node.child, root_case, visited)
                root_case.case_items.append(
                    CaseItem(
                        condition=Expression(node.unique_id),
                        statements=[
                            Statement(f"{node.to_string()};"),
                            NonBlockingSubsitution(
                                lvalue=root_case.condition.to_string(),
                                rvalue=next_state,
                            ),
                        ],
                    )
                )
                self._context.global_vars[node.unique_id] = len(root_case.case_items)
                # if node.optimal_child:
                #     next_state = self.graph_build_node(
                #         node.optimal_child, root_case, visited
                #     )
                #     root_case.case_items.append(
                #         CaseItem(
                #             condition=Expression(node.unique_id),
                #             statements=[
                #                 Statement(f"{node.to_string()};"),
                #                 NonBlockingSubsitution(
                #                     lvalue=root_case.condition.to_string(),
                #                     rvalue=next_state,
                #                 ),
                #             ],
                #         )
                #     )
            return node.unique_id
        if isinstance(node, ir.IfElseNode):
            if node.unique_id not in visited:
                visited.add(node.unique_id)
                then_state = self.graph_build_node(node._true_edge, root_case, visited)
                else_state = self.graph_build_node(node._false_edge, root_case, visited)
                root_case.case_items.append(
                    CaseItem(
                        condition=Expression(node.unique_id),
                        statements=[
                            IfElse(
                                condition=Expression(node._condition.to_string()),
                                then_body=[
                                    NonBlockingSubsitution(
                                        root_case.condition.to_string(), then_state
                                    )
                                ],
                                else_body=[
                                    NonBlockingSubsitution(
                                        root_case.condition.to_string(), else_state
                                    )
                                ],
                            )
                        ],
                    )
                )
                self._context.global_vars[node.unique_id] = len(root_case.case_items)
            return node.unique_id
        if isinstance(node, ir.YieldNode):
            if node.unique_id not in visited:
                visited.add(node.unique_id)
                next_state = self.graph_build_node(node.child, root_case, visited)
                stmts = [
                    NonBlockingSubsitution(f"_out{i}", v.to_string())
                    for i, v in enumerate(node._stmts)
                ] + [NonBlockingSubsitution("_valid", "1")]
                root_case.case_items.append(
                    CaseItem(
                        condition=Expression(node.unique_id),
                        statements=[
                            *stmts,
                            NonBlockingSubsitution(
                                lvalue=root_case.condition.to_string(),
                                rvalue=next_state,
                            ),
                        ],
                    )
                )
                self._context.global_vars[node.unique_id] = len(root_case.case_items)
            return node.unique_id
        if isinstance(node, ir.Edge):
            if node.unique_id not in visited:
                visited.add(node.unique_id)
                return self.graph_build_node(node.child, root_case, visited)
            return "bruvlmao"
        if isinstance(node, ir.DoneNode):
            if node.unique_id not in visited:
                visited.add(node.unique_id)
                root_case.case_items.append(
                    CaseItem(
                        condition=Expression(node.unique_id),
                        statements=[
                            NonBlockingSubsitution("_done", "1"),
                        ],
                    )
                )
                self._context.global_vars[node.unique_id] = len(root_case.case_items)
            return node.unique_id
        raise RuntimeError(f"Unexpected type {type(node)} {node}")

    @staticmethod
    def __get_start_ifelse(root: Statement, global_vars: dict[str, str]):
        """
        if (_start) begin
            <var> = <value>;
            ...
        end else begin
        ...
        end
        """
        then_body: list[Statement] = [NonBlockingSubsitution("_done", "0")]
        then_body += [
            NonBlockingSubsitution(key, str(val)) for key, val in global_vars.items()
        ]
        block = IfElse(
            Expression("_start"),
            then_body,
            [root],
        )
        return block

    @property
    def module(self):
        """
        Get Verilog module
        """
        assert isinstance(self._module, Module)
        return self._module

    def get_module_lines(self):
        """
        Get Verilog module as Lines
        """
        return self.module.to_lines()

    def get_module_str(self):
        """
        Get Verilog module as string
        """
        return str(self.get_module_lines())

    def new_testbench(self, test_cases: list[tuple[str]]):
        """
        Creates testbench with multiple test cases

        Each element of test_cases represents a single test case
        """

        def make_display_stmt():
            """
            Creates a display statement for valid + outputs

            $display("%0d, ...", _valid, ...);
            """
            string = '$display("%0d, '
            string += "%0d, " * (len(self._context.output_vars) - 1)
            string += '%0d", _valid'
            for var in self._context.output_vars:
                string += f", {var}"
            string += ");"
            return Statement(literal=string)

        assert isinstance(self._context, ir.Context)
        decl: list[Declaration] = []
        decl.append(Declaration("_clock", size=1, is_reg=True))
        decl.append(Declaration("_start", size=1, is_reg=True))
        decl += [
            Declaration(var, is_signed=True, is_reg=True)
            for var in self._context.input_vars
        ]
        decl += [Declaration(var, is_signed=True) for var in self._context.output_vars]

        decl.append(Declaration("_done", size=1))
        decl.append(Declaration("_valid", size=1))

        ports = {
            decl.name: decl.name for decl in decl
        }  # Caution: expects decl to only contain declarations

        setups: list[Statement] = list(decl)
        setups.append(Instantiation(self._context.name, "DUT", ports))

        setups.append(Statement(literal="always #5 _clock = !_clock;"))

        initial_body: list[Statement | While] = []  # TODO: replace with Sequence
        initial_body.append(BlockingSubsitution("_clock", "0"))
        initial_body.append(BlockingSubsitution("_start", "0"))
        initial_body.append(AtNegedgeStatement(Expression("_clock")))
        initial_body.append(Statement())

        for i, test_case in enumerate(test_cases):
            # setup for new test case
            initial_body.append(Statement(comment=f"Test case {i}: {str(test_case)}"))
            for i, var in enumerate(self._context.input_vars):
                initial_body.append(BlockingSubsitution(var, str(test_case[i])))
            initial_body.append(BlockingSubsitution("_start", "1"))

            initial_body.append(AtNegedgeStatement(Expression("_clock")))

            # wait for done signal
            while_body: list[Statement] = []
            while_body.append(BlockingSubsitution("_start", "0"))
            while_body.append(make_display_stmt())
            while_body.append(AtNegedgeStatement(Expression("_clock")))

            initial_body.append(While(condition=Expression("!_done"), body=while_body))
            # initial_body.append(make_display_stmt())
            initial_body.append(Statement())

        initial_body.append(Statement(literal="$finish;"))

        initial_loop = Initial(body=initial_body)

        if self._context:
            module = Module(
                f"{self._context.name}_tb",
                [],
                [],
                body=setups + [initial_loop],
                add_default_ports=False,
            )
            return module
        raise RuntimeError("Needs the context")

    def new_testbench_lines(self, test_cases: list[tuple[str]]):
        """
        New Testbench as lines
        """
        return self.new_testbench(test_cases).to_lines()

    def new_testbench_str(self, test_cases: list[tuple[str]]):
        """
        New testbench as str
        """
        return str(self.new_testbench_lines(test_cases))


class CaseBuilder:
    """
    Creates a case statement for the IR Graph
    """

    def __init__(self, root: ir.Vertex):
        # Member Vars
        self.visited: set[str] = set()
        self.case = Case(expression=Expression("_state"), case_items=[])

        # Member Funcs
        instance = itertools.count()
        self.next_unique = lambda: next(instance)

        # Work
        self.case.case_items.append(self.new_caseitem(root))
        # logging.info(self.case.to_string())

    def new_caseitem(self, root: ir.Vertex):
        """
        Creates a new case item with the root's unique id as identifier
        """
        stmts = self.do_vertex(root)
        item = CaseItem(condition=Expression(root.unique_id), statements=stmts)

        return item

    def do_vertex(self, vertex: ir.Vertex):
        """
        Processes a node
        """
        assert isinstance(vertex, ir.Vertex)
        if vertex.unique_id in self.visited and not isinstance(vertex, ir.DoneNode):
            logging.info(f"already visited {vertex}")
            return [Statement("bruv")]
        self.visited.add(vertex.unique_id)

        stmts: list[Statement] = []

        if isinstance(vertex, ir.DoneNode):
            stmts += [
                NonBlockingSubsitution("_done", "1"),
                NonBlockingSubsitution(
                    self.case.condition.to_string(), "_statelmaodone"
                ),
            ]

        elif isinstance(vertex, ir.AssignNode):
            stmts.append(NonBlockingSubsitution(str(vertex.lvalue), str(vertex.rvalue)))
            stmts += self.do_edge(vertex.optimal_child)

        elif isinstance(vertex, ir.IfElseNode):
            then_body = self.do_edge(vertex.optimal_true_edge)
            else_body = self.do_edge(vertex.optimal_false_edge)
            stmts.append(
                IfElse(
                    condition=Expression(str(vertex.condition)),
                    then_body=then_body,
                    else_body=else_body,
                )
            )

        elif isinstance(vertex, ir.YieldNode):
            outputs = [
                NonBlockingSubsitution(f"_out{i}", str(expr))
                for i, expr in enumerate(vertex._stmts)
            ] + [NonBlockingSubsitution("_valid", "1")]
            state_change = []

            if isinstance(vertex.optimal_child.optimal_child, ir.DoneNode):
                outputs.append(NonBlockingSubsitution("_done", "1"))
            state_change.append(
                NonBlockingSubsitution(
                    "_state", str(vertex.optimal_child.optimal_child.unique_id)
                )
            )
            if vertex.optimal_child.optimal_child.unique_id not in self.visited:
                self.case.case_items.append(
                    self.new_caseitem(vertex.optimal_child.optimal_child)
                )

            # stmts += outputs + self.do_edge(vertex.optimal_child)
            stmts += outputs + state_change

        else:
            raise TypeError(type(vertex))

        return stmts

    def do_edge(self, edge: ir.Edge):
        """
        Processes a edge
        """
        if isinstance(edge, ir.NonClockedEdge):
            return self.do_vertex(edge.optimal_child)
        if isinstance(edge, ir.ClockedEdge):
            if edge.optimal_child.unique_id not in self.visited:
                self.case.case_items.append(self.new_caseitem(edge.optimal_child))
            return [NonBlockingSubsitution("_state", str(edge.optimal_child.unique_id))]
        raise RuntimeError(f"{type(edge)}")
