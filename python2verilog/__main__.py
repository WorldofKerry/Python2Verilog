"""
Converts Python generator functions to synthesizable Verilog.

For sample Python inputs,
visit https://github.com/WorldofKerry/Python2Verilog/tree/main/tests/integration/data
"""
import logging

import argparse
import os
import ast
import warnings
from typing import Optional
from python2verilog import ir

from python2verilog.api import convert_for_debug
from python2verilog.api.api import convert_from_cli

logging.root.setLevel(logging.INFO)


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
        "-n",
        "--name",
        type=str,
        help="Name of function to be converted, defaults to python filename stem",
        default="",
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
        help="Set to a value greater than 0 for optimizations, \
            higher values will use more logic cells",
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

    if args.name == "":
        args.name = input_file_stem
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

        context = ir.Context(
            name=args.name,
        )
        if args.test_cases:
            context.test_cases = ast.literal_eval(args.test_cases)
        test_cases = ast.literal_eval(args.test_cases) if args.test_cases else []

        print(f"TEST CASES: {context.test_cases}")
        verilog_code_gen, _ = convert_from_cli(
            code=python,
            func_name=args.name,
            optimization_level=args.optimization_level,
            test_cases=test_cases,
            file_path=input_file_path,
        )

        with open(
            os.path.abspath(args.output), mode="w+", encoding="utf8"
        ) as module_file:
            module_file.write(verilog_code_gen.get_module_lines().to_string())

        if args.test_cases != "":
            with open(
                os.path.abspath(args.testbench), mode="w+", encoding="utf8"
            ) as tb_file:
                tb_file.write(
                    verilog_code_gen.new_testbench(ast.literal_eval(args.test_cases))
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
