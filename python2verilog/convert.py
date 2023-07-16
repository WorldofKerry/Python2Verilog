"""
To run the basic conversion as a script
"""

import argparse
import os
import ast
from .frontend import Generator2Ast
from .backend.codegen import Verilog

parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument(
    "input_file",
    type=str,
    help="Input file containing a python generator function",
)

input_file_path = parser.parse_args().input_file
input_file_stem = os.path.splitext(input_file_path)[0]

parser.add_argument(
    "-o",
    "--output_file",
    help="Output file for System Verilog module",
    default=input_file_stem + ".sv",
)

args = parser.parse_args()

with open(os.path.abspath(input_file_path), mode="r", encoding="utf8") as python_file:
    python = python_file.read()
    _locals = {}
    exec(python, None, _locals)  # grab's exec's populated scoped variables

    tree = ast.parse(python)
    function = tree.body[0]
    ir_generator = Generator2Ast(function)
    output = ir_generator.parse_statements(function.body, "")
    verilog = Verilog()
    verilog.from_ir(output, ir_generator.global_vars)
    verilog.setup_from_python(function)

    with open(
        os.path.abspath(args.output_file), mode="w", encoding="utf8"
    ) as module_file:
        module_file.write(verilog.get_module().to_string())
