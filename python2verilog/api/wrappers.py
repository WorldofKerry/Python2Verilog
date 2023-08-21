"""
Wrappers
"""

from python2verilog import ir
from python2verilog.backend import verilog
from python2verilog.frontend.generator2ir import Generator2Graph
from python2verilog.optimizer.optimizer import OptimizeGraph


def context_to_verilog(context: ir.Context):
    """
    Converts a context to verilog and its ir

    :return: (context, ir)
    """
    ir_root, context = Generator2Graph(context).results
    if context.optimization_level > 0:
        OptimizeGraph(ir_root, threshold=context.optimization_level - 1)
    return verilog.CodeGen(ir_root, context), ir_root


def context_to_text(context: ir.Context):
    """
    Converts a context to module and testbench strings

    :return: (module, testbench) pair of strings
    """
    ver_code_gen, _ = context_to_verilog(context)
    return ver_code_gen.get_module_str(), ver_code_gen.new_testbench_str()
