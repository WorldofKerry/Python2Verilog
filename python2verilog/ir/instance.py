"""
Generator Instance
"""

from dataclasses import dataclass

from python2verilog.ir.expressions import Var


@dataclass(frozen=True)
class Instance:
    """
    Instance
    """

    # pylint: disable=too-many-instance-attributes
    func_name: str
    valid_signal: Var
    done_signal: Var
    clock_signal: Var
    start_signal: Var
    reset_signal: Var
    ready_signal: Var
    outputs: list[Var]
