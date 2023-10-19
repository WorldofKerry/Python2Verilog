"""
Protocol signals used by the converter
"""

from dataclasses import dataclass, fields
from typing import Iterator

from python2verilog.ir.expressions import ExclusiveVar, Var


@dataclass
class InstanceSignals:
    """
    Signals that are often named differently for each instance
    """

    # pylint: disable=too-many-instance-attributes
    start: Var = Var("start")
    done: ExclusiveVar = ExclusiveVar("done")

    ready: Var = Var("ready")
    valid: ExclusiveVar = ExclusiveVar("valid")

    prefix: str = ""

    @staticmethod
    def apply_prefix(name: str, prefix: str):
        """
        Creates a Var with prefix
        """
        return ExclusiveVar(f"{prefix}{name}", f"_{prefix}{name}")

    def __post_init__(self):
        self.start = self.apply_prefix("start", self.prefix)
        self.done = self.apply_prefix("done", self.prefix)
        self.ready = self.apply_prefix("ready", self.prefix)
        self.valid = self.apply_prefix("valid", self.prefix)


@dataclass
class ProtocolSignals(InstanceSignals):
    """
    Protocol signals

    Includes ready, valid, clock, reset, done, etc.
    """

    reset: Var = Var("reset")
    clock: Var = Var("clock")

    prefix: str = ""

    def variable_values(self) -> Iterator[Var]:
        """
        Values
        """
        for _, value in self.variable_items():
            yield value

    def variable_items(self) -> Iterator[tuple[str, Var]]:
        """
        Key, Value pairs
        """
        for key, value in self.__dict__.items():
            if isinstance(value, Var):
                yield key, value

    def instance_specific_items(self) -> Iterator[tuple[str, Var]]:
        """
        Get the instance-specific signals
        """
        instance_signals = map(lambda field_: field_.name, fields(InstanceSignals))
        for key, value in self.variable_items():
            if key in instance_signals:
                yield key, value

    def instance_specific_values(self) -> Iterator[Var]:
        """
        Get the instance-specific signals
        """
        for _, value in self.instance_specific_items():
            yield value
