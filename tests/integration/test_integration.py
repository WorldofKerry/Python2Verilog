import ast
import configparser
import logging
import os
import re
import subprocess
import time
import unittest
import warnings
from typing import Any, Optional

import networkx as nx
import pandas as pd
import pytest
from matplotlib import pyplot as plt

from python2verilog import ir, simulation
from python2verilog.api.python import py_to_codegen
from python2verilog.simulation.iverilog import run_with_fifos, run_with_files
from python2verilog.utils.assertions import get_typed
from python2verilog.utils.visualization import make_visual

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
            testbench_args: Optional[dict[Any, Any]] = None,
            **kwargs,
        ):
            """
            :param test_cases: `name: [(test0_arg0, test0_arg1, ...), (test1_arg0, ...), ...]`
            """
            self.all_statistics: list[dict] = []
            self.test_cases = test_cases
            if not testbench_args:
                testbench_args = {}
            self.testbench_args = testbench_args
            super().__init__(*args, **kwargs)

        def test_integration(self):
            if self.args.first_test:
                logging.info("Only first test being ran")
            for level in self.args.optimization_levels:
                for name, cases in self.test_cases.items():
                    if self.args.first_test:
                        cases = [cases[0]]
                    with self.subTest(msg=name):
                        logging.info(
                            f"Testing function `{name}` with -O{level} on `{cases}`"
                        )
                        self.run_test(
                            name,
                            cases,
                            self.args,
                            "data",
                            f"_{name}_O{level}_",
                            optimization_level=level,
                            testbench_args=self.testbench_args,
                        )
            if self.all_statistics:
                if self.testbench_args["random_wait"] is False:
                    test_that_are_too_slow = []
                    for stat in self.all_statistics:
                        if (
                            "-O" in stat["Func Name"]
                            and "-O0" not in stat["Func Name"]
                            and "multiplier" not in stat["Func Name"]
                            and "testing" not in stat["Func Name"]
                        ):
                            slowness_multiplier = stat["Ver Clks"] / (
                                stat["Py Yields"] + 8
                            )  # + x for loop and end overhead
                            if slowness_multiplier > 1.30:
                                test_that_are_too_slow.append(stat)
                    self.assertFalse(
                        test_that_are_too_slow,
                        "\n"
                        + "\n".join([str(test) for test in test_that_are_too_slow]),
                    )
                self.all_statistics.sort(key=lambda e: e["Func Name"])
                df = pd.DataFrame(
                    self.all_statistics, columns=self.all_statistics[0].keys()
                )
                title = f" Statistics for {self.__class__.__name__} "
                table = df.to_markdown()
                table_width = len(table.partition("\n")[0])
                pad = table_width - len(title)
                result = (
                    "\n"
                    + "=" * (pad // 2)
                    + title
                    + "=" * (pad // 2 + pad % 2)
                    + "\n"
                    + table
                )
                logging.warning(result)
            else:
                logging.critical("No stats found")

        def run_test(
            self,
            function_name: str,
            test_cases: list[tuple],
            args: dict,
            dir: str,
            prefix: str,
            optimization_level: int,
            testbench_args: dict[Any, Any],
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

            with open(FILES_IN_ABS_DIR["python"]) as python_file:
                python_text = python_file.read()

            logging.debug(f"executing python")
            _locals = dict()
            exec(python_text, None, _locals)  # grab's exec's populated scoped variables

            logging.debug("parsing to AST")

            tree = ast.parse(python_text)

            expected = []
            for test_case in test_cases:
                logging.debug(f"test case: {test_case}")
                generator_inst = _locals[function_name](*test_case)
                size = None

                for iter_, raw_output in enumerate(generator_inst):
                    if isinstance(raw_output, int):
                        output = (raw_output,)
                    else:
                        output = raw_output
                    get_typed(output, tuple)

                    if size is None:
                        size = len(output)
                    else:
                        assert (
                            len(output) == size
                        ), f"All generator yields must be same length tuple, but got {output} of length {len(output)} when previous yields had length {size}"

                    for e in output:
                        assert isinstance(e, int)

                    expected.append(raw_output)

                    if iter_ >= 100000:
                        err_msg = f"capped generator outputs to {iter_} iterations"
                        logging.error(err_msg)
                        raise RuntimeError(err_msg)

            statistics = {
                "Func Name": f"{function_name} -O{optimization_level}",
                "Py Yields": len(expected),
            }
            self.all_statistics.append(statistics)

            logging.debug("generating expected")

            if args.write:
                logging.debug("writing expected")
                with open(FILES_IN_ABS_DIR["expected"], mode="w") as expected_file:
                    for output in expected:
                        expected_file.write(f"{str(output)[1:-1]}\n")

                logging.debug("making visual and writing it")
                make_visual(
                    _locals[function_name](*test_cases[0]),
                    FILES_IN_ABS_DIR["expected_visual"],
                )

                logging.info("writing ast dump")
                with open(FILES_IN_ABS_DIR["ast_dump"], mode="w") as ast_dump_file:
                    ast_dump_file.write(ast.dump(tree, indent="  "))

            logging.debug(f"Finished executing python and created expected")

            logging.debug(
                f'For debugging, try running `iverilog -s {function_name}_tb {FILES_IN_ABS_DIR["module"]} {FILES_IN_ABS_DIR["testbench"]} -o iverilog.log && unbuffer vvp iverilog.log && rm iverilog.log`'
            )

            verilog, root = py_to_codegen(
                code=python_text,
                function_name=function_name,
                extra_test_cases=test_cases,
                file_path=FILES_IN_ABS_DIR["python"],
                optimization_level=optimization_level,
                write=False,
            )

            if args.write:
                with open(FILES_IN_ABS_DIR["cytoscape"], mode="w") as cyto_file:
                    cyto_file.write(str(ir.create_cytoscape_elements(root)))

            logging.debug("Generating module and tb")

            module_str = verilog.get_module_str()
            tb_str = verilog.get_testbench_str(**testbench_args)

            logging.debug("Writing module and tb")

            if args.write:
                with open(FILES_IN_ABS_DIR["module"], mode="w") as module_file:
                    module_file.write(module_str)

                with open(FILES_IN_ABS_DIR["testbench"], mode="w") as testbench_file:
                    testbench_file.write(tb_str)

            time_started = time.time()
            if args.write:
                stdout, stderr = run_with_files(
                    f"{function_name}_tb",
                    {
                        FILES_IN_ABS_DIR["module"]: module_str,
                        FILES_IN_ABS_DIR["testbench"]: tb_str,
                    },
                    timeout=1 + len(expected) // 64,
                )
            else:
                stdout, stderr = run_with_fifos(
                    f"{function_name}_tb",
                    {
                        FILES_IN_ABS_DIR["module_fifo"]: module_str,
                        FILES_IN_ABS_DIR["testbench_fifo"]: tb_str,
                    },
                    timeout=1 + len(expected) // 64,
                )
            time_delta_ms = (time.time() - time_started) * 1000

            self.assertTrue(
                stdout and not stderr,
                f"\nVerilog simulation on {function_name}, with:\
                    \n{stderr}\n{FILES_IN_ABS_DIR['module']}\
                        \n{FILES_IN_ABS_DIR['testbench']}, \
                            produced stdout: {stdout}",
            )

            actual_raw = list(simulation.parse_stdout(stdout))

            if args.write:
                with open(FILES_IN_ABS_DIR["actual"], mode="w") as filtered_f:
                    for output in actual_raw:
                        filtered_f.write(str(output)[1:-1] + "\n")

            statistics["Ver Clks"] = len(actual_raw)
            statistics["Simu (ms)"] = time_delta_ms

            try:
                filtered_actual = list(simulation.strip_signals(actual_raw))
            except simulation.UnknownValue as e:
                logging.error(
                    f"{function_name} {len(filtered_actual)} {e}\n{FILES_IN_ABS_DIR['module']}\n{FILES_IN_ABS_DIR['testbench']}"
                )

            if args.write:
                with open(FILES_IN_ABS_DIR["filtered_actual"], mode="w") as filtered_f:
                    for output in filtered_actual:
                        filtered_f.write(f"{str(output)[1:-1]}\n")

                make_visual(filtered_actual, FILES_IN_ABS_DIR["actual_visual"])

            err_msg = "\nactual_coords vs expected_coords"
            if len(filtered_actual) == len(expected):
                err_msg += ", lengths are same, likely a rounding or sign error"
            err_msg += f"\n{FILES_IN_ABS_DIR['filtered_actual']}\n{FILES_IN_ABS_DIR['expected']}\n{FILES_IN_ABS_DIR['module']}\n{FILES_IN_ABS_DIR['testbench']}"
            self.assertEqual(
                filtered_actual,
                expected,
                err_msg,
            )

            if args.write and args.synthesis:
                logging.info("Running yosys for synthesis")
                with subprocess.Popen(
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
                ) as syn_process:
                    syn_process.wait()
                    stdout = syn_process.stdout.read()
                    stderr = syn_process.stderr.read()

                self.assertFalse(stderr.strip())
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

                        except ValueError:
                            continue

                    data[key] = value
                for key, value in data.items():
                    statistics[key] = value

            for key in fifos:
                os.remove(FILES_IN_ABS_DIR[key])


@pytest.mark.usefixtures("argparse")
class Performance(BaseTestCases.BaseTest):
    def __init__(self, *args, **kwargs):
        BaseTestCases.BaseTest.__init__(
            self, TEST_CASES, *args, testbench_args={"random_wait": False}, **kwargs
        )


@pytest.mark.usefixtures("argparse")
class Correctness(BaseTestCases.BaseTest):
    def __init__(self, *args, **kwargs):
        BaseTestCases.BaseTest.__init__(
            self, TEST_CASES, *args, testbench_args={"random_wait": True}, **kwargs
        )


# For easier testing of a specific function
@pytest.mark.usefixtures("argparse")
class Testing(BaseTestCases.BaseTest):
    def __init__(self, *args, **kwargs):
        BaseTestCases.BaseTest.__init__(
            self,
            {"testing": TEST_CASES["testing"]},
            *args,
            testbench_args={"random_wait": True},
            **kwargs,
        )
