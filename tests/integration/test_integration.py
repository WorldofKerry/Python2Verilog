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
from dataclasses import dataclass
import networkx as nx
from matplotlib import pyplot as plt

from python2verilog.backend.verilog import IrToVerilog, CaseBuilder
from python2verilog.frontend import Generator2Graph
from python2verilog.optimizer import optimizer
from python2verilog.convert import *
from python2verilog.ir import *
from python2verilog.utils.visualization import make_visual


@dataclass
class Statistics:
    """
    Holds a test's statistics
    """

    function_name: str = "Unspecified"
    python_yields: int = -1
    verilog_clocks: int = -1
    module_num_chars: int = -1

    def __iter__(self):
        yield from self.values()

    def values(self):
        return self.__dict__.values()

    def keys(self):
        return self.__dict__.keys()


@pytest.mark.usefixtures("argparse")  # creates self.args
class TestMain(unittest.TestCase):
    all_statistics: list[Statistics] = []

    def run_test(
        self,
        function_name: str,
        test_cases: list[tuple],
        args: dict,
        dir: str = f"data/{pathlib.Path(__file__).stem.replace('test_', '')}/",
    ):
        """
        Stats will only be gathered on the last test
        """
        logging.info(f"starting test for {dir}/{function_name}")

        assert len(test_cases) > 0, "Please include at least one test case"

        if args.first_test:
            test_cases = [test_cases[0]]

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
        FILES_IN_ABS_DIR = {
            key: os.path.join(ABS_DIR, value)
            for key, value in config["file_names"].items()
        }
        fifos = {
            "module_fifo": "module_fifo.sv",
            "testbench_fifo": "tb_fifo.sv",
        }  # named pipe in memory
        FILES_IN_ABS_DIR.update(
            {key: os.path.join(ABS_DIR, value) for key, value in fifos.items()}
        )
        for key in fifos:
            if os.path.exists(FILES_IN_ABS_DIR[key]):
                os.remove(FILES_IN_ABS_DIR[key])
            os.mkfifo(FILES_IN_ABS_DIR[key])

        logging.info(f"executing python")

        with open(FILES_IN_ABS_DIR["python"]) as python_file:
            python = python_file.read()
            _locals = dict()
            exec(python, None, _locals)  # grab's exec's populated scoped variables

            tree = ast.parse(python)

            expected = []
            for test_case in test_cases:
                generator_inst = _locals[function_name](*test_case)
                size = None
                for tupl in generator_inst:
                    assert isinstance(
                        tupl, tuple
                    ), "Yield tuples only, use (x,) for single-width tuples"

                    if size is None:
                        size = len(tupl)
                    else:
                        assert (
                            len(tupl) == size
                        ), f"All generator yields must be same length tuple, but got {tupl} of length {len(tupl)} when previous yields had length {size}"

                    for e in tupl:
                        assert isinstance(e, int)

                    expected.append(tupl)

            statistics = Statistics(
                function_name=function_name, python_yields=len(expected)
            )

            logging.info("generating expected")

            if args.write:
                with open(FILES_IN_ABS_DIR["expected"], mode="w") as expected_file:
                    for tupl in expected:
                        if len(tupl) > 1:
                            expected_file.write(f"{str(tupl)[1:-1]}\n")
                        else:
                            expected_file.write(
                                f"{str(tupl)[1:-2]}\n"
                            )  # remove trailing comma
                make_visual(
                    _locals[function_name](*test_cases[0]),
                    FILES_IN_ABS_DIR["expected_visual"],
                )

                with open(FILES_IN_ABS_DIR["ast_dump"], mode="w") as ast_dump_file:
                    ast_dump_file.write(ast.dump(tree, indent="  "))

            logging.info(f"finished executing python and created expected")

            iverilog_cmd = f'iverilog -s {function_name}_tb {FILES_IN_ABS_DIR["module_fifo"]} {FILES_IN_ABS_DIR["testbench_fifo"]} -o iverilog.log && unbuffer vvp iverilog.log && rm iverilog.log\n'
            process = subprocess.Popen(
                iverilog_cmd,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            function = tree.body[0]

            ir, context = Generator2Graph(function).results
            optimizer.graph_optimize(ir, threshold=0)
            case_builder = CaseBuilder(ir)
            # __states = IrToVerilog.create_nonclocked_list(
            #     ir, set(), [f"state {ir.unique_id}"], set()
            # )
            # print("DONEEEEEEEE")
            # for __state in __states:
            #     print(__state)

            # print("\n\nnext")
            # optimizer.graph_optimize(ir.child.child)
            # print("\n\nnextasdf3eefwe\n")
            verilog = IrToVerilog.from_graph_ir(ir, context)

            if args.write:
                with open(FILES_IN_ABS_DIR["cytoscape"], mode="w") as cyto_file:
                    cyto_file.write(str(create_cytoscape_elements(ir)))

                adjacency_list = create_networkx_adjacency_list(ir)
                g = nx.DiGraph(adjacency_list)

                plt.figure(figsize=(40, 40))
                nx.draw(
                    g,
                    with_labels=True,
                    font_weight="bold",
                    arrowsize=30,
                    node_size=4000,
                    node_shape="s",
                    node_color="#00b4d9",  # Light Blue
                )
                plt.savefig(FILES_IN_ABS_DIR["ir_dump"])
                plt.clf()
                plt.cla()
                plt.close()

            module_str = verilog.get_module_lines().to_string()
            statistics.module_num_chars = len(
                module_str.replace("\n", "").replace(" ", "")
            )
            tb_str = verilog.new_testbench(test_cases).to_string()

            with open(FILES_IN_ABS_DIR["module_fifo"], mode="w") as module_file:
                module_file.write(module_str)

            with open(FILES_IN_ABS_DIR["testbench_fifo"], mode="w") as testbench_file:
                testbench_file.write(tb_str)

            if args.write:
                with open(FILES_IN_ABS_DIR["module"], mode="w") as module_file:
                    module_file.write(module_str)

                with open(FILES_IN_ABS_DIR["testbench"], mode="w") as testbench_file:
                    testbench_file.write(tb_str)
            process.wait()

            if args.write and args.synthesis:
                syn_process = subprocess.Popen(
                    [
                        "yosys",
                        "-QT",
                        "-fverilog",
                        FILES_IN_ABS_DIR["module"],
                        "-pstat",
                    ],
                    shell=True,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                syn_process.wait()
                stdout = syn_process.stdout.read()

                print(f"STDOUTTTTT {stdout}")
                stats = stdout[stdout.find("Printing statistics:") :]
                print(stats)

                def snake_case(text):
                    return re.sub(r"[\W_]+", "_", text).strip("_").lower()

                lines = stats.strip().splitlines()
                data = {}

                for line in lines:
                    if ":" in line:
                        key, value = line.split(":")
                        key = snake_case(key)
                        value = int(value.strip())
                    else:
                        value = int(line.strip())
                        key = snake_case(data["number_of_cells"] + "_" + line.strip())

                    data[key] = value
                print(data)

            stderr_str = process.stderr.read()
            if stderr_str != "":
                warnings.warn(
                    f"ERROR with running verilog simulation on {function_name}, with: {stderr_str}"
                )

            actual_str = process.stdout.read()

            actual_raw: list[list[str]] = []
            for line in actual_str.splitlines():
                row = [elem.strip() for elem in line.split(",")]
                actual_raw.append(row)

            statistics.verilog_clocks = len(actual_raw)
            TestMain.all_statistics.append(statistics)

            filtered_actual = []
            for row in actual_raw:
                if row[0] == "1":
                    filtered_actual.append(tuple([int(elem) for elem in row[1:]]))

            if args.write:
                with open(FILES_IN_ABS_DIR["filtered_actual"], mode="w") as filtered_f:
                    for tupl in filtered_actual:
                        filtered_f.write(" " + str(tupl)[1:-1] + "\n")

                make_visual(filtered_actual, FILES_IN_ABS_DIR["actual_visual"])

            actual_coords = set(filtered_actual)
            expected_coords = set(expected)

            self.assertEqual(
                actual_coords - expected_coords,
                set(),
                f"str(actual_coords - expected_coords) <-- extra coordinates, actual expected: {str(actual_coords)} {str(expected_coords)}",
            )
            self.assertEqual(
                expected_coords - actual_coords,
                set(),
                f"str(expected_coords - actual_coor <-- missing coordinates, actual expected: {str(actual_coords)} {str(expected_coords)}",
            )

            for key in fifos:
                os.remove(FILES_IN_ABS_DIR[key])

            return "Running test"

    def tearDownClass():
        df = pd.DataFrame(
            TestMain.all_statistics, columns=TestMain.all_statistics[0].keys()
        )
        print("\n" + df.to_markdown(index=False))

    def test_circle_lines(self):
        test_cases = [(21, 37, 7), (89, 45, 43)]
        self.run_test("circle_lines", test_cases, self.args)

    def test_happy_face(self):
        test_cases = [(50, 51, 7), (86, 97, 43)]
        self.run_test("happy_face", test_cases, self.args)

    def test_rectangle_filled(self):
        test_cases = [(32, 84, 5, 7), (64, 78, 34, 48)]
        self.run_test("rectangle_filled", test_cases, self.args)

    def test_rectangle_lines(self):
        test_cases = [(32, 84, 5, 7), (84, 96, 46, 89)]
        self.run_test("rectangle_lines", test_cases, self.args)

    def test_fib(self):
        test_cases = [(10,), (35,)]
        self.run_test("fib", test_cases, self.args)

    # def test_tree_bfs(self):
    #     binary_tree = [1, 7, 8, 2, 4, 6, 8, 6, 9]
    #     self.run_test(
    #         "tree_bfs", [(binary_tree, [420] * len(binary_tree), len(binary_tree))]
    #     )

    def test_testing(self):
        test_cases = [(15,)]
        self.run_test("testing", test_cases, self.args)
