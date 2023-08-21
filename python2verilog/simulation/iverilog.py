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


def write_data_to_paths(path_to_data: dict[str, str]):
    """
    Writes data to respective path
    """
    for path, data in path_to_data.items():
        with open(path, mode="w") as file:
            file.write(data)


def run_cmd_with_fifos(
    command: str, input_fifos: dict[str, str], timeout: typing.Optional[int] = None
):
    """
    Runs a command that uses fifos as input. DO NOT use this function with regular files.

    :param input_fifos: absolute file path of fifos -> data to write

    :return: (stdout, stderr/exception)
    """
    process = subprocess.Popen(
        command,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    write_data_to_paths(input_fifos)

    try:
        process.wait(timeout=timeout)
        return process.stdout.read(), process.stderr.read()
    except subprocess.TimeoutExpired as e:
        logging.error(e)
        process.terminate()
        return None, str(e)


def run_cmd_with_files(
    command: str, input_files: dict[str, str], timeout: typing.Optional[int] = None
):
    """
    Runs a command that uses files as input. DO NOT use this function with regular fifos.

    :param input_files: absolute file path of files -> data to write

    :return: (stdout, stderr/exception)
    """
    write_data_to_paths(input_files)

    process = subprocess.Popen(
        command,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        process.wait(timeout=timeout)
        return process.stdout.read(), process.stderr.read()
    except subprocess.TimeoutExpired as e:
        logging.error(e)
        process.terminate()
        return None, str(e)
