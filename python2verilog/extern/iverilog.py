"""
Icarious Verilog CLI Abstractions
"""

import logging
import os
import signal
import subprocess
import tempfile
from typing import Generator, Iterable, Optional


def make_iverilog_cmd(top_level_module: str, files: Iterable[str]):
    """
    Returns an iverilog command

    :param files: set of absolute paths to files required for simulation
    """
    cmd = f"iverilog -g2005-sv -s {top_level_module} "
    cmd += " ".join(files) + " "
    # pylint: disable=consider-using-with
    cache_file = tempfile.NamedTemporaryFile(mode="r", encoding="utf8")
    cache_path = cache_file.name
    cmd += f"-o {cache_path} && unbuffer vvp {cache_path} && rm {cache_path}"
    return cmd


def write_data_to_paths(path_to_data: dict[str, str]):
    """
    Writes data to respective path
    """
    logging.debug("Writing data to paths start")
    for path, data in path_to_data.items():
        with open(path, mode="w", encoding="utf8") as file:
            logging.debug(f"Writing {len(data)} to {file.name}")
            file.write(data)
    logging.debug("Writing data to paths done")


def run_cmd_with_fifos(
    command: str, input_fifos: dict[str, str], timeout: Optional[int] = None
):
    """
    Runs a command that uses fifos as input. DO NOT use this function with regular files.

    :param input_fifos: absolute file path of fifos -> data to write

    :return: (stdout, stderr/exception)
    """
    # pylint: disable=subprocess-popen-preexec-fn
    with subprocess.Popen(
        command,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    ) as process:
        write_data_to_paths(input_fifos)

        try:
            logging.debug(f"Waiting on process for {timeout}s")
            process.wait(timeout=timeout)
            assert process.stdout
            assert process.stderr
            return process.stdout.read(), process.stderr.read()
        except subprocess.TimeoutExpired as e:
            logging.error(e)
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            assert process.stdout
            assert process.stderr
            return process.stdout.read(), process.stderr.read()


def run_cmd_with_files(
    command: str, input_files: dict[str, str], timeout: Optional[int] = None
):
    """
    Runs a command that uses files as input. DO NOT use this function with regular fifos.

    :param input_files: absolute file path of files -> data to write

    :return: (stdout, stderr/exception)
    """
    write_data_to_paths(input_files)
    # pylint: disable=subprocess-popen-preexec-fn
    with subprocess.Popen(
        command,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    ) as process:
        try:
            logging.debug(f"Waiting on process for {timeout}s")
            process.wait(timeout=timeout)
            assert process.stdout
            assert process.stderr
            return process.stdout.read(), process.stderr.read()
        except subprocess.TimeoutExpired as e:
            logging.error(e)
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            assert process.stdout
            assert process.stderr
            return process.stdout.read(), process.stderr.read()


def run_iverilog_with_fifos(
    top_level_module: str,
    input_fifos: dict[str, str],
    timeout: Optional[int] = None,
):
    """
    Run iverilog with fifos

    :return: (stdout, stderr/exception)
    """
    iverilog_cmd = make_iverilog_cmd(
        top_level_module=top_level_module,
        files=input_fifos.keys(),
    )
    logging.debug(f"Running {iverilog_cmd}")
    return run_cmd_with_fifos(
        command=iverilog_cmd, input_fifos=input_fifos, timeout=timeout
    )


def run_iverilog_with_files(
    top_level_module: str,
    input_files: dict[str, str],
    timeout: Optional[int] = None,
):
    """
    Run iverilog with files

    :return: (stdout, stderr/exception)
    """
    iverilog_cmd = make_iverilog_cmd(
        top_level_module=top_level_module,
        files=input_files.keys(),
    )
    logging.debug(f"Running {iverilog_cmd}")
    return run_cmd_with_files(
        command=iverilog_cmd, input_files=input_files, timeout=timeout
    )


def parse_stdout(stdout: str) -> Generator[tuple[str, ...], None, None]:
    """
    Implementation-specific (based on testbench output)

    Yields the signals and outputs for a display statement

    :return: [valid, ready, output0, output1, ...]
    """
    for line in stdout.splitlines():
        yield tuple(elem.strip() for elem in line.split(","))


def strip_signals(
    actual_raw: Iterable[tuple[str, ...]],
) -> Generator[tuple[int, ...], None, None]:
    """
    Implementation-specific (based on testbench output)

    Assumes assumes first two signals to be valid and wait

    [valid, ready, output0, output1, ...]

    Only yields a row if both valid and ready

    Throws if both valid and ready, but an output is 'x'

    :return: [output0, output1, ...]
    """
    for row in actual_raw:
        assert len(row) >= 2  # [valid, ready, ...]
        if row[0] == "1" and row[1] == "1":
            try:
                yield tuple(int(elem) for elem in row[2:])
            except ValueError as e:
                raise ValueError(f"Unknown logic value in outputs {row}") from e
