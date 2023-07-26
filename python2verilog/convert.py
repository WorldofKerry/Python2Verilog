"""
To run the basic conversion as a CLI script
"""

import argparse
import os
import ast
import warnings
from typing import Optional
from .frontend import Generator2List, Generator2Graph
from .backend.verilog import Verilog
from .optimizer import optimizer


def convert_list(func: ast.FunctionDef, optimization_level: int):
    """
    Wrapper for common Python to Verilog conversion
    """
    ir_root, context = Generator2List(func).get_results()
    if optimization_level > 0:
        ir_root = optimizer.optimize_if(ir_root)
        ir_root = optimizer.combine_cases(ir_root)
        ir_root = optimizer.remove_unreferenced_states(ir_root)
    return Verilog.from_list_ir(ir_root, context)


def convert_graph(func: ast.FunctionDef, optimization_level: int):
    """
    Wrapper for Python to Verilog conversion
    """

    ir, context = Generator2Graph(func).results
    if optimization_level > 0:
        pass
    return Verilog.from_graph_ir(ir, context)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "input_file",
        type=str,
        help="Input file containing a python generator function",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for System Verilog module",
        default="",
    )

    TESTBENCH_ARG = parser.add_argument(
        "-t",
        "--testbench",
        type=str,
        help="Output file for System Verilog testbench",
        default="",
    )

    parser.add_argument(
        "-c",
        "--test-cases",
        type=str,
        help='A list of test cases for testbench. \
            Required to output testbench. E.g. `-c "[(1, 2, 3, 4)]"`',
        default="",
    )
    parser.add_argument(
        "-O",
        "--optimization-level",
        type=int,
        help="Optimization level of output, between 0 and 3 inclusive, \
            \nhigher means more optimized but may be more difficult to reason",
        default=0,
    )

    def get_default_tb_filename(stem: str):
        """
        Gets default testbench filename
        """
        return stem + "_tb.sv"

    args = parser.parse_args()
    input_file_path = parser.parse_args().input_file
    input_file_stem = os.path.splitext(input_file_path)[0]
    if args.output == "":
        args.output = input_file_stem + ".sv"

    if args.testbench == "":
        args.testbench = get_default_tb_filename(input_file_stem)

    with open(
        os.path.abspath(input_file_path), mode="r", encoding="utf8"
    ) as python_file:
        python = python_file.read()
        _locals: dict[str, str] = {}
        exec(python, None, _locals)  # grab's exec's populated scoped variables

        tree = ast.parse(python)
        function = tree.body[0]
        assert isinstance(function, ast.FunctionDef)
        verilog = convert_list(function, args.optimization_level)

        with open(
            os.path.abspath(args.output), mode="w+", encoding="utf8"
        ) as module_file:
            module_file.write(verilog.get_module_lines().to_string())

        if args.test_cases != "":
            with open(
                os.path.abspath(args.testbench), mode="w+", encoding="utf8"
            ) as tb_file:
                tb_file.write(
                    verilog.new_testbench(ast.literal_eval(args.test_cases))
                    .to_lines()
                    .to_string()
                )
        elif args.test_cases == "" and args.testbench != get_default_tb_filename(
            input_file_stem
        ):
            raise argparse.ArgumentError(
                TESTBENCH_ARG,
                f"testbench path provided by no test cases provided \
                    {args.test_cases}, {args.testbench}",
            )
