"""
Protocol signals used by the converter
"""

from dataclasses import dataclass, fields
from typing import Iterator

from python2verilog.ir.expressions import Var


@dataclass(frozen=True)
class InstanceSignals:
    """
    Signals that are often named differently for each instance
    """

    # pylint: disable=too-many-instance-attributes
    start: Var
    done: Var

    ready: Var
    valid: Var


@dataclass(frozen=True)
class ProtocolSignals(InstanceSignals):
    """
    Protocol signals

    Includes ready, valid, clock, reset, done, etc.
    """

    reset: Var = Var("reset")
    clock: Var = Var("clock")

    def __iter__(self):
        for key in self.__dict__:
            yield key

    def values(self) -> Iterator[Var]:
        """
        Values
        """
        for value in self.__dict__.values():
            yield value

    def items(self) -> Iterator[tuple[str, Var]]:
        """
        Key, Value pairs
        """
        for key, value in self.__dict__.items():
            yield key, value

    def instance_specific_items(self) -> Iterator[tuple[str, Var]]:
        """
        Get the instance-specific signals
        """
        instance_signals = map(lambda field_: field_.name, fields(InstanceSignals))
        for key, value in self.items():
            if key in instance_signals:
                yield key, value

    def instance_specific_values(self) -> Iterator[Var]:
        """
        Get the instance-specific signals
        """
        for _, value in self.instance_specific_items():
            yield value
