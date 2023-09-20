"""
Functions that take text as input
"""


import copy
import logging

from python2verilog import ir
from python2verilog.backend import verilog
from python2verilog.frontend.generator2ir import Generator2Graph
from python2verilog.optimizer.optimizer import OptimizeGraph
from python2verilog.utils.assertions import get_typed


def context_to_codegen(context: ir.Context):
    """
    Converts a context to verilog and its ir

    :return: (codegen, ir)
    """
    context = copy.copy(context)
    ir_root, context = Generator2Graph(context).results
    logging.debug(
        f"context to codegen {ir_root.unique_id} {context.name} -O{context.optimization_level}"
    )
    if context.optimization_level > 0:
        OptimizeGraph(ir_root, threshold=context.optimization_level - 1)
    return verilog.CodeGen(ir_root, context), ir_root


def context_to_verilog(context: ir.Context) -> tuple[str, str]:
    """
    Converts a context to a verilog module and testbench

    :return: (module, testbench)
    """
    get_typed(context, ir.Context)
    ver_code_gen, _ = context_to_codegen(context)

    module_str = ver_code_gen.get_module_str()
    tb_str = ver_code_gen.get_testbench_str()

    return module_str, tb_str


def context_to_verilog_and_dump(context: ir.Context) -> tuple[str, str, str]:
    """
    Converts a context to a verilog module, testbench, and cytoscape str

    :return: (module, testbench, cytoscape_dump) pair
    """
    get_typed(context, ir.Context)
    ver_code_gen, ir_root = context_to_codegen(context)

    module_str = ver_code_gen.get_module_str()
    tb_str = ver_code_gen.get_testbench_str()

    return module_str, tb_str, ir.create_cytoscape_elements(ir_root)
