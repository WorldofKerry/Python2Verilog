"""
Protocol signals used by the converter
"""

from dataclasses import dataclass
from typing import Generator

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

    def __iter__(self):
        for key in self.__dict__:
            yield key

    def values(self) -> Generator[Var, None, None]:
        """
        Values
        """
        for value in self.__dict__.values():
            yield value

    def items(self) -> Generator[tuple[str, Var], None, None]:
        """
        Key, Value pairs
        """
        for key, value in self.__dict__.items():
            yield key, value