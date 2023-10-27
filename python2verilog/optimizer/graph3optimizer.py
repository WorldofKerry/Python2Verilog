import python2verilog.ir.graph2 as ir
from python2verilog.ir.graph2 import *
from python2verilog.optimizer.graph2optimizer import Transformer
from python2verilog.optimizer.helpers import backwards_replace


class insert_phis(Transformer):
    """
    On basic blocks
    """

    def apply(self):
        return super().apply()

    def one_block(self, source: BasicBlock):
        """
        Insert Phis for one block
        """
        dom_frontier: set[BasicBlock] = set(self.dominance_frontier(source))

        for block in dom_frontier:
            block_args = BlockHead()

            for var in self.get_operations_lhs(source):
                block_args.phis[var] = {source: None}

            block.statements.insert(0, block_args)

        return self

    def get_operations_lhs(self, block: BasicBlock):
        """
        Gets LHSs of operations
        """
        for operation in block.statements:
            if isinstance(operation, AssignNode):
                yield operation.lvalue


class rename_blocks(Transformer):
    def __init__(self, graph: CFG, *, apply: bool = True):
        super().__init__(graph, apply=apply)
        self.visited = set()
        self.var_counter = {}
        self.stacks: dict[expr.Var, list[expr.Var]] = {}
        self.var_mapping = {}

    def apply(self, block: BasicBlock):
        self.rename(block)
        return self

    def rename(self, b: BasicBlock, recursion: bool = True):
        """
        Based on slide 33 of
        https://ics.uci.edu/~yeouln/course/ssa.pdf
        """
        if b in self.visited:
            return
        self.visited.add(b)

        for statement in b.statements:
            if isinstance(statement, BlockHead):
                self.update_phi_lhs(statement)

        for statement in b.statements:
            self.update_lhs_rhs_stack(statement)

        for s in self.adj_list[b]:
            # For each successor in CFG
            assert guard(s, BasicBlock)
            for statement in s.statements:
                if isinstance(statement, ir.BlockHead):
                    for var, phi in statement.phis.items():
                        phi[b] = self.stacks[self.var_mapping[var]][-1]

        if recursion:
            # DFS in dominator tree
            for s in self.dominator_tree().get(b, set()):
                self.rename(s)

        # Unwind stack
        for statement in b.statements:
            if isinstance(statement, ir.BlockHead):
                for key in statement.phis:
                    self.stacks[self.var_mapping[key]].pop()
            if isinstance(statement, ir.AssignNode):
                self.stacks[self.var_mapping[statement.lvalue]].pop()

    def update_phi_lhs(self, block: BlockHead):
        replacement = {}
        for v, phis in block.phis.items():
            vn = self.gen_name(v)
            replacement[vn] = phis
        block.phis = replacement

    def update_lhs_rhs_stack(self, statement: Element):
        if isinstance(statement, AssignNode):
            statement.rvalue = backwards_replace(
                statement.rvalue, self.make_mapping(self.stacks)
            )
            statement.lvalue = self.gen_name(statement.lvalue)
        if isinstance(statement, BranchNode):
            statement.expr = backwards_replace(
                statement.expr, self.make_mapping(self.stacks)
            )

    def gen_name(self, var: expr.Var):
        # Make new unqiue name
        count = self.var_counter.get(var, 0)
        new_var = expr.Var(f"%{var.py_name}{count}")
        self.var_counter[var] = count + 1

        # Update var stack
        stack = self.stacks.get(var, [])
        stack.append(new_var)
        self.stacks[var] = stack

        # Remember mapping
        self.var_mapping[new_var] = var

        return new_var

    def make_mapping(self, mapping_stack: dict[expr.Var, list[expr.Var]]):
        """
        Converts mapping stacks to mapping

        e.g. for an item a -> [x, y, z], the resulting mapping has a -> z
        """
        return {key: value[-1] for key, value in mapping_stack.items()}
