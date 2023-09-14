"""
Protocol signals used by the converter
"""

import warnings
from dataclasses import dataclass, fields
from typing import Generator

from python2verilog.ir.expressions import Var


@dataclass(frozen=True)
class InstanceSignals:
    """
    Signals that are often named differently for each instance
    """

    # pylint: disable=too-many-instance-attributes
    start_signal: Var
    done_signal: Var

    ready_signal: Var
    valid_signal: Var


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

    def instance_specific(self) -> Generator[tuple[str, Var], None, None]:
        """
        Get the instance-specific signals
        """
        instance_signals = map(lambda field_: field_.name, fields(InstanceSignals))
        # warnings.warn(str(instance_signals))
        for key, value in self.items():
            if key in instance_signals:
                yield key, value
