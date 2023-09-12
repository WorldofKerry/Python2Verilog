"""
Protocol signals used by the converter
"""

from dataclasses import dataclass

from python2verilog.ir.expressions import Var


@dataclass(frozen=True)
class ProtocolSignals:
    """
    Protocol signals

    Includes ready, valid, clock, reset, done, etc.
    """

    # pylint: disable=too-many-instance-attributes
    start_signal: Var
    done_signal: Var

    ready_signal: Var
    valid_signal: Var

    reset_signal: Var = Var("reset")
    clock_signal: Var = Var("clock")
