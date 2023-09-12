"""
An instance of a generator

Can be created from a context
"""

from dataclasses import dataclass

from python2verilog.ir.expressions import Var


@dataclass(frozen=True)
class Instance:
    """
    Instance

    :param module_name: generator function name
    :param var: variable name assigned to generator instance
    """

    # pylint: disable=too-many-instance-attributes
    module_name: str
    var: Var
    valid_signal: Var
    done_signal: Var
    clock_signal: Var
    start_signal: Var
    reset_signal: Var
    ready_signal: Var
    inputs: list[Var]
    outputs: list[Var]
