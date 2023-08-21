"""
Icarious Verilog CLI Abstractions
"""

import logging
import subprocess
import tempfile
import typing


def make_iverilog_cmd(top_level_module: str, files: list[str]):
    """
    Returns an iverilog command

    :param files: list of absolute paths to files
    """
    cmd = f"iverilog -s {top_level_module} "
    cmd += " ".join(files) + " "
    cache_file = tempfile.NamedTemporaryFile(mode="r", encoding="utf8")
    cache_path = cache_file.name
    cmd += f"-o {cache_path} && unbuffer vvp {cache_path} && rm {cache_path}"
    return cmd


def run_fifo_command(
    command: str, input_fifos: dict[str, str], timeout: typing.Optional[int] = None
):
    """
    :param input_fifos: absolute file path -> data to write
    :return: (stdout, stderr)
    """
    process = subprocess.Popen(
        command,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    for path, data in input_fifos:
        with open(path, mode="w") as file:
            file.write(data)

    if timeout:
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            logging.error(e)
            process.terminate()
            raise e

    return (process.stdout.read(), process.stderr.read())
