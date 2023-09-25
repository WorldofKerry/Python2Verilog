"""
Parses Verilog display statements
"""

import logging
from typing import Generator, Iterable, Union


def parse_stdout(stdout: str) -> Generator[tuple[str, ...], None, None]:
    """
    Implementation-specific (based on testbench output)
    Yields the signals and outputs for a display statement
    :return: [valid, ready, output0, output1, ...]
    """
    for line in stdout.splitlines():
        yield tuple(elem.strip() for elem in line.split(","))


def strip_signals(
    actual_raw: Iterable[tuple[str, ...]], include_invalid: bool
) -> Generator[Union[tuple[int, ...], int], None, None]:
    """
    Implementation-specific (based on testbench output)
    Assumes assumes first two signals to be valid and wait
    [valid, ready, output0, output1, ...]
    Only yields a row if both valid and ready
    Throws if both valid and ready, but an output is 'x'
    :return: [output0, output1, ...]
    """
    for row in actual_raw:
        if len(row) >= 2:  # [valid, ready, ...]
            if include_invalid:
                if row[1] == "1":  # ready == 1
                    outputs = row[2:]
                    if len(outputs) == 1:
                        yield outputs[0]
                    else:
                        yield tuple(elem for elem in outputs)
            else:
                if row[0] == "1" and row[1] == "1":
                    try:
                        outputs = row[2:]
                        if len(outputs) == 1:
                            yield int(outputs[0])
                        else:
                            yield tuple(int(elem) for elem in outputs)
                    except ValueError as e:
                        raise UnknownValue(
                            f"Unknown logic value in outputs {row}"
                        ) from e
        else:
            if "$finish" in " ".join(row):
                pass
            else:
                raise ValueError(f"Skipped parsing {row}")


class UnknownValue(Exception):
    """
    An unexpected 'x' or 'z' was encountered
    """
