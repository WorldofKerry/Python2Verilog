"""
Creates testbench from context and FSM
"""
from python2verilog import ir
from python2verilog.backend.verilog import ast as ver
from python2verilog.ir.expressions import UInt
from python2verilog.optimizer.helpers import backwards_replace
from python2verilog.utils.lines import Lines


class Testbench(ver.Module):
    """
    Testbench
    """
