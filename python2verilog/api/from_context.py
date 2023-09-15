"""
Functions that take text as input
"""


from python2verilog import ir
from python2verilog.backend import verilog
from python2verilog.frontend.generator2ir import Generator2Graph
from python2verilog.optimizer.optimizer import OptimizeGraph
from python2verilog.utils.smart_asserts import get_typed


def context_to_verilog(context: ir.Context):
    """
    Converts a context to verilog and its ir

    :return: (codegen, ir)
    """
    ir_root, context = Generator2Graph(context).results
    if context.optimization_level > 0:
        OptimizeGraph(ir_root, threshold=context.optimization_level - 1)
    return verilog.CodeGen(ir_root, context), ir_root


def context_to_text(context: ir.Context) -> tuple[str, str]:
    """
    Converts a context to a verilog module and testbench str

    :return: (module, testbench) pair
    """
    get_typed(context, ir.Context)
    ver_code_gen, _ = context_to_verilog(context)

    module_str = ver_code_gen.get_module_str()
    tb_str = ver_code_gen.get_testbench_str()

    return module_str, tb_str


def context_to_text_and_dump(context: ir.Context) -> tuple[str, str, str]:
    """
    Converts a context to a verilog module, testbench, and cytoscape str

    :return: (module, testbench, cytoscape_dump) pair
    """
    get_typed(context, ir.Context)
    ver_code_gen, ir_root = context_to_verilog(context)

    module_str = ver_code_gen.get_module_str()
    tb_str = ver_code_gen.get_testbench_str()

    return module_str, tb_str, ir.create_cytoscape_elements(ir_root)
