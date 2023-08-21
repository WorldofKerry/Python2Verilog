"""
Icarious Verilog CLI Abstractions
"""

import logging
import tempfile
import typing


def run_iverilog(top_level_module: str, files: list[str]):
    """
    Runs iverilog

    :param files: list of absolute paths to files
    """
    cmd = f"iverilog -s {top_level_module} "
    cmd += " ".join(files) + " "
    with tempfile.NamedTemporaryFile(mode="r", encoding="utf8") as cache_file:
        cache_path = cache_file.name
        cmd += f"-o {cache_path} && unbuffer vvp {cache_path} && rm {cache_path}"
        logging.error(cmd)
