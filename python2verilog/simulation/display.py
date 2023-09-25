"""
Parses Verilog display statements
"""

import logging
from typing import Generator, Iterable, Iterator, Union


def parse_stdout(stdout: str) -> Iterator[tuple[str, ...]]:
    """
    Implementation-specific (based on testbench output)
    Yields the signals and outputs for a display statement
    :return: [valid, ready, output0, output1, ...]
    """
    for line in stdout.splitlines():
        yield tuple(elem.strip() for elem in line.split(","))


def strip_ready(
    actual: Iterable[Union[tuple[str, ...], str]]
) -> Iterator[Union[tuple[str, ...], str]]:
    """
    Assumes first two signals to be ready and valid,
    such that a row is [ready, valid, output0, output1, ...]

    Removes tailing messages, e.g. `$finish`.

    :return: [valid, output0, output1, ...]
    """
    for row in actual:
        if len(row) >= 2:  # [ready, valid ...]
            if row[0] == "1":  # ready signal
                outputs = row[1:]
                if len(outputs) == 1:
                    yield outputs[0]
                else:
                    yield tuple(elem for elem in outputs)
        else:
            if "$finish" in " ".join(row):
                pass
            else:
                raise ValueError(f"Unexpected row {row}")


def strip_valid(
    actual: Iterable[Union[tuple[str, ...], str]]
) -> Iterator[Union[tuple[int, ...], int]]:
    """
    Assumes first signal to be valid,
    such that a row is [valid, output0, output1, ...]

    Throws if ready, but an output is 'x'.

    Removes tailing messages, e.g. `$finish`.

    :return: [output0, output1, ...]
    """
    for row in actual:
        if len(row) >= 2:  # [valid ...]
            if row[0] == "1":  # valid signal
                try:
                    outputs = row[1:]
                    if len(outputs) == 1:
                        yield int(outputs[0])
                    else:
                        yield tuple(int(elem) for elem in outputs)
                except ValueError as e:
                    raise UnknownValue(f"Unknown logic value in outputs {row}") from e
        else:
            if "$finish" in " ".join(row):
                pass
            else:
                raise ValueError(f"Unexpected row {row}")


class UnknownValue(Exception):
    """
    An unexpected 'x' or 'z' was encountered
    """
