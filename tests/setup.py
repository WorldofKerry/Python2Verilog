import os
import sys

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(src_path)

import python2verilog


def output(filename: str, suffix: str = "actual", ext: str = "txt"):
    output_filename = filename.replace(".py", f"_{suffix}.{ext}")
    return open(output_filename, "w")

def input(filename: str, suffix: str = "actual", ext: str = "txt"): 
    input_filename = filename.replace(".py", f"_{suffix}.{ext}")
    return open(input_filename, "r")

__all__ = ["python2verilog", "output", "input"]
