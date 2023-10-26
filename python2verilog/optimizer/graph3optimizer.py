from python2verilog.ir.graph2 import *
from python2verilog.optimizer.graph2optimizer import Transformer


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
            block_args = BlockHeadNode()

            for var in self.get_operations_lhs(source):
                print(f"{type(var)=}")
                block_args.phis[var] = {block: None}

            block.operations.insert(0, block_args)

        print(f"{dom_frontier=}")
        return self

    def get_operations_lhs(self, block: BasicBlock):
        """
        Gets LHSs of operations
        """
        for operation in block.operations:
            if isinstance(operation, AssignNode):
                yield operation.lvalue
