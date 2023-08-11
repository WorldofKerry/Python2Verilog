from typing import Callable
import unittest
import ast
import warnings
import os
import configparser
import subprocess
import csv
import copy
import re
import logging
import pathlib
import pandas as pd
import pytest
import networkx as nx
from matplotlib import pyplot as plt
from abc import abstractmethod

from python2verilog.backend.verilog import CodeGen, CaseBuilder
from python2verilog.frontend import Generator2Graph
from python2verilog import ir
from python2verilog.api import convert_graph_debug
from python2verilog.utils.assertions import assert_type
from tools.visualization import make_visual
from .cases import TEST_CASES


class BaseTestCases:
    """
    Wrapper for test
    """

    class BaseTest(unittest.TestCase):
        """
        Class that is ran
        """

        def __init__(
            self,
            test_cases: dict[str, list[tuple[int, ...]]],
            *args,
            **kwargs,
        ):
            """
            :param test_cases: `name: [(test0_arg0, test0_arg1, ...), (test1_arg0, ...), ...]`
            """
            self.all_statistics: list[dict] = []
            self.test_cases = test_cases
            super().__init__(*args, **kwargs)

        def test_integration(self):
            if self.args.first_test:
                logging.info("Only first test being ran")
            for level in self.args.optimization_levels:
                for name, cases in self.test_cases.items():
                    if self.args.first_test:
                        cases = [cases[0]]
                    with self.subTest(msg=name):
                        logging.info(f"Testing `{name}` at with -O{level} on `{cases}`")
                        self.run_test(
                            name,
                            cases,
                            self.args,
                            "data",
                            f"_{name}_O{level}_",
                            optimization_level=level,
                        )
            self.all_statistics.sort(key=lambda e: e["function_name"])
            if self.all_statistics:
                df = pd.DataFrame(
                    self.all_statistics, columns=self.all_statistics[0].keys()
                )
                logging.info("\n" + df.to_markdown(index=False))
            else:
                logging.warning("No stats collected")
                warnings.warn("No stats collected")

        def run_test(
            self,
            function_name: str,
            test_cases: list[tuple],
            args: dict,
            dir: str,
            prefix: str,
            optimization_level: int,
        ):
            """
            Stats will only be gathered on the last test
            """
            logging.debug(f"starting test for {dir}/{function_name}")

            assert len(test_cases) > 0, "Please include at least one test case"

            for test_case in test_cases:
                assert isinstance(
                    test_case, tuple
                ), "Inputs should be tuples, use (x,) for single-width tuple"
                assert len(test_case) > 0, "Please have data in the test case"

            ABS_DIR = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), dir, function_name
            )

            assert os.path.exists(
                ABS_DIR
            ), f"Test on `{ABS_DIR}` failed, as that directory does not exist"

            config = configparser.ConfigParser()
            config.read(os.path.join(ABS_DIR, "config.ini"))
            # The python file shall not be name-mangled
            FILES_IN_ABS_DIR = {
                key: os.path.join(ABS_DIR, f"{prefix}{value}")
                if key != "python"
                else os.path.join(ABS_DIR, f"{value}")
                for key, value in config["file_names"].items()
            }
            fifos = {
                "module_fifo": f"{prefix}module_fifo.sv",
                "testbench_fifo": f"{prefix}testbench_fifo.sv",
            }  # named pipe in memory
            FILES_IN_ABS_DIR.update(
                {key: os.path.join(ABS_DIR, value) for key, value in fifos.items()}
            )
            for key in fifos:
                if os.path.exists(FILES_IN_ABS_DIR[key]):
                    os.remove(FILES_IN_ABS_DIR[key])
                os.mkfifo(FILES_IN_ABS_DIR[key])

            logging.debug(f"executing python")

            with open(FILES_IN_ABS_DIR["python"]) as python_file:
                python = python_file.read()
                _locals = dict()
                exec(python, None, _locals)  # grab's exec's populated scoped variables

                tree = ast.parse(python)

                expected = []
                for test_case in test_cases:
                    generator_inst = _locals[function_name](*test_case)
                    size = None
                    for output in generator_inst:
                        if isinstance(output, int):
                            output = (output,)
                        assert_type(output, tuple)

                        if size is None:
                            size = len(output)
                        else:
                            assert (
                                len(output) == size
                            ), f"All generator yields must be same length tuple, but got {output} of length {len(output)} when previous yields had length {size}"

                        for e in output:
                            assert isinstance(e, int)

                        expected.append(output)

                statistics = {
                    "function_name": f"{function_name} -O{optimization_level}",
                    "py_yields": len(expected),
                }

                logging.debug("generating expected")

                if args.write:
                    with open(FILES_IN_ABS_DIR["expected"], mode="w") as expected_file:
                        for output in expected:
                            if len(output) > 1:
                                expected_file.write(f"{str(output)[1:-1]}\n")
                            else:
                                expected_file.write(
                                    f"{str(output)[1:-2]}\n"
                                )  # remove trailing comma
                    make_visual(
                        _locals[function_name](*test_cases[0]),
                        FILES_IN_ABS_DIR["expected_visual"],
                    )

                    with open(FILES_IN_ABS_DIR["ast_dump"], mode="w") as ast_dump_file:
                        ast_dump_file.write(ast.dump(tree, indent="  "))

                logging.debug(f"Finished executing python and created expected")

                iverilog_cmd = f'iverilog -s {function_name}_tb {FILES_IN_ABS_DIR["module_fifo"]} {FILES_IN_ABS_DIR["testbench_fifo"]} -o iverilog.log && unbuffer vvp iverilog.log && rm iverilog.log\n'

                logging.debug(f"Running `{iverilog_cmd}`")
                logging.debug(
                    f'For debugging, try running `iverilog -s {function_name}_tb {FILES_IN_ABS_DIR["module"]} {FILES_IN_ABS_DIR["testbench"]} -o iverilog.log && unbuffer vvp iverilog.log && rm iverilog.log`'
                )

                process = subprocess.Popen(
                    iverilog_cmd,
                    shell=True,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                function = tree.body[0]
                verilog, root = convert_graph_debug(
                    function, optimization_level=optimization_level
                )
                if args.write:
                    with open(FILES_IN_ABS_DIR["cytoscape"], mode="w") as cyto_file:
                        cyto_file.write(str(ir.create_cytoscape_elements(root)))

                    # adjacency_list = ir.create_networkx_adjacency_list(root)
                    # g = nx.DiGraph(adjacency_list)

                    # plt.figure(figsize=(40, 40))
                    # nx.draw(
                    #     g,
                    #     with_labels=True,
                    #     font_weight="bold",
                    #     arrowsize=30,
                    #     node_size=4000,
                    #     node_shape="s",
                    #     node_color="#00b4d9",  # Light Blue
                    # )
                    # plt.savefig(FILES_IN_ABS_DIR["ir_dump"])
                    # plt.clf()
                    # plt.cla()
                    # plt.close()

                logging.debug("Generating module and tb")

                module_str = verilog.get_module_lines().to_string()
                statistics["module_nchars"] = len(
                    module_str.replace("\n", "").replace(" ", "")
                )
                tb_str = verilog.new_testbench(test_cases).to_string()

                logging.debug("Writing module and tb")
                if args.write:
                    with open(FILES_IN_ABS_DIR["module"], mode="w") as module_file:
                        module_file.write(module_str)

                    with open(
                        FILES_IN_ABS_DIR["testbench"], mode="w"
                    ) as testbench_file:
                        testbench_file.write(tb_str)

                with open(FILES_IN_ABS_DIR["module_fifo"], mode="w") as module_file:
                    module_file.write(module_str)

                with open(
                    FILES_IN_ABS_DIR["testbench_fifo"], mode="w"
                ) as testbench_file:
                    testbench_file.write(tb_str)

                try:
                    process.wait(timeout=max(1, len(expected)))  # May need adjusting

                    logging.debug("Getting iverilog stderr")

                    stderr_str = process.stderr.read()
                    if stderr_str != "":
                        warnings.warn(
                            f"ERROR with running verilog simulation on {function_name}, with: {stderr_str}"
                        )

                    logging.debug("Getting iverilog stdout")

                    actual_str = process.stdout.read()

                    actual_raw: list[list[str]] = []
                    for line in actual_str.splitlines():
                        row = [elem.strip() for elem in line.split(",")]
                        actual_raw.append(row)

                    if args.write:
                        with open(FILES_IN_ABS_DIR["actual"], mode="w") as filtered_f:
                            for output in actual_raw:
                                filtered_f.write(str(output)[1:-1] + "\n")

                    statistics["ver_clks"] = len(actual_raw)
                    self.all_statistics.append(statistics)

                    filtered_actual = []
                    for row in actual_raw:
                        if row[0] == "1":
                            filtered_actual.append(
                                tuple([int(elem) for elem in row[1:]])
                            )

                    if args.write:
                        with open(
                            FILES_IN_ABS_DIR["filtered_actual"], mode="w"
                        ) as filtered_f:
                            for output in filtered_actual:
                                filtered_f.write(str(output)[1:-1] + "\n")

                        make_visual(filtered_actual, FILES_IN_ABS_DIR["actual_visual"])

                    err_msg = "\nactual_coords vs expected_coords"
                    if len(filtered_actual) == len(expected):
                        err_msg += ", lengths are same, likely a rounding or sign error"
                    err_msg += f"\n{FILES_IN_ABS_DIR['filtered_actual']}\n{FILES_IN_ABS_DIR['expected']}\n{FILES_IN_ABS_DIR['module']}"
                    self.assertEqual(
                        filtered_actual,
                        expected,
                        err_msg,
                    )

                    if args.write and args.synthesis:
                        syn_process = subprocess.Popen(
                            " ".join(
                                [
                                    "yosys",
                                    "-QT",
                                    "-fverilog",
                                    FILES_IN_ABS_DIR["module"],
                                    "-pstat",
                                ]
                            ),
                            shell=True,
                            text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        syn_process.wait()
                        stdout = syn_process.stdout.read()
                        stderr = syn_process.stderr.read()
                        if stderr:
                            warnings.warn(stderr)

                        stats = stdout[stdout.find("Printing statistics.") :]

                        def snake_case(text):
                            return re.sub(r"[\W_]+", "_", text).strip("_").lower()

                        lines = stats.strip().splitlines()
                        data = {}

                        for line in lines:
                            if ":" in line:
                                key, value = line.split(":")
                                key = snake_case(key).split("number_of_")[-1]
                                value = int(value.strip())
                            else:
                                try:
                                    index = line.find("$") + 10
                                    value = int(line[index:].strip())
                                    key = line[:index].strip()[1:]
                                    data[key] = value

                                except ValueError as _:
                                    continue

                            data[key] = value
                        for key, value in data.items():
                            statistics[key] = value

                except subprocess.TimeoutExpired as e:
                    logging.warning(e)
                    warnings.warn(e)
                    process.terminate()

                for key in fifos:
                    os.remove(FILES_IN_ABS_DIR[key])


@pytest.mark.usefixtures("argparse")
class Graph(BaseTestCases.BaseTest):
    def __init__(self, *args, **kwargs):
        BaseTestCases.BaseTest.__init__(self, TEST_CASES, *args, **kwargs)


# @pytest.mark.usefixtures("argparse")
# class GraphOpti1(BaseTestCases.BaseTest, OptimizedGraphBase):
#     def __init__(self, *args, **kwargs):
#         OptimizedGraphBase.__init__(
#             self, optimization_levels=int(self.__class__.__name__[-1])
#         )
#         BaseTestCases.BaseTest.__init__(self, TEST_CASES, *args, **kwargs)


# @pytest.mark.usefixtures("argparse")
# class GraphOpti2(BaseTestCases.BaseTest, OptimizedGraphBase):
#     def __init__(self, *args, **kwargs):
#         OptimizedGraphBase.__init__(
#             self, optimization_levels=int(self.__class__.__name__[-1])
#         )
#         BaseTestCases.BaseTest.__init__(self, TEST_CASES, *args, **kwargs)


# @pytest.mark.usefixtures("argparse")
# class GraphOpti3(BaseTestCases.BaseTest, OptimizedGraphBase):
#     def __init__(self, *args, **kwargs):
#         OptimizedGraphBase.__init__(
#             self, optimization_levels=int(self.__class__.__name__[-1])
#         )
#         BaseTestCases.BaseTest.__init__(self, TEST_CASES, *args, **kwargs)


# @pytest.mark.usefixtures("argparse")
# class GraphOpti8(BaseTestCases.BaseTest, OptimizedGraphBase):
#     def __init__(self, *args, **kwargs):
#         OptimizedGraphBase.__init__(
#             self, optimization_levels=int(self.__class__.__name__[-1])
#         )
#         BaseTestCases.BaseTest.__init__(self, TEST_CASES, *args, **kwargs)


# # For easier testing
# @pytest.mark.usefixtures("argparse")
# class GraphTesting(BaseTestCases.BaseTest, OptimizedGraphBase):
#     def __init__(self, *args, **kwargs):
#         OptimizedGraphBase.__init__(self, optimization_levels=1)
#         BaseTestCases.BaseTest.__init__(
#             self, {"testing": TEST_CASES["testing"]}, *args, **kwargs
#         )
