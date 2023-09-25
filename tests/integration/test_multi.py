"""
Test suite for functions that call other functions
"""

import inspect
import logging
import os
import re
import subprocess
import warnings
from pathlib import Path
from types import FunctionType
from typing import Union
from unittest import TestCase

import pandas as pd
import pytest
from parameterized import parameterized, parameterized_class

from python2verilog import (
    Modes,
    get_actual_raw,
    get_context,
    get_expected,
    namespace_to_file,
    namespace_to_verilog,
    verilogify,
)
from python2verilog.api.verilogify import get_actual
from python2verilog.backend.verilog.config import CodegenConfig
from python2verilog.simulation import iverilog
from python2verilog.simulation.display import strip_ready, strip_valid

from .functions import *
from .utils import make_tuple, name_func

PARAMETERS = [
    ([olympic_logo, colored_circle], [(10, 10, 4), (13, 13, 7)]),
    ([dupe, hrange], [(0, 1, 10), (3, 7, 25)]),
]


@pytest.mark.usefixtures("argparse")
class TestComplete(TestCase):
    statistics: list[dict] = []
    write: bool = False

    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_multi_performance(
        self, funcs: list[FunctionType], test_cases: list[Union[tuple[int, ...], int]]
    ):
        for opti_level in self.args.optimization_levels:
            ns = {}

            for func in reversed(funcs):  # First function is tested upon
                verilogified = verilogify(
                    namespace=ns, optimization_level=opti_level, mode=Modes.OVERWRITE
                )(func)

            for case in test_cases:
                case = make_tuple(case)
                verilogified(*case)

            config = CodegenConfig(random_ready=False)
            module, testbench = namespace_to_verilog(ns, config)
            test_name = str(
                Path(__file__).parent
                / (self.__dict__["_testMethodName"] + f"::O{opti_level}")
            )
            if self.args.write:
                TestComplete.write = True
                file_stem = test_name.replace("::", "_")
                namespace_to_file(file_stem, ns, config)
                context = get_context(verilogified)
                cmd = iverilog.make_cmd(
                    context.testbench_name,
                    [file_stem + ".sv", file_stem + "_tb.sv"],
                )
                logging.info(cmd)

            expected = list(get_expected(verilogified))
            actual_with_invalid = list(
                strip_ready(
                    get_actual_raw(
                        verilogified,
                        module,
                        testbench,
                        timeout=1 + len(expected) // 64,
                    )
                )
            )
            actual = list(strip_valid(actual_with_invalid))
            logging.info(
                f"Actual len {len(actual)}: {str(actual[:min(len(actual), 5)])[:-1]}, ...]"
            )
            self.assertTrue(len(actual) > 0, f"{actual} {expected}")
            self.assertListEqual(actual, expected)

            statistics = {
                "Test Name": test_name.split("/")[-1],
                "Py Yields": len(expected),
                "Ver Clks": len(actual_with_invalid),
            }
            if self.args.synthesis and self.args.write:
                logging.info("Running yosys for synthesis")
                with subprocess.Popen(
                    " ".join(
                        [
                            "yosys",
                            "-QT",
                            "-fverilog",
                            file_stem + ".sv",
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

            TestComplete.statistics.append(statistics)

    @classmethod
    def tearDownClass(cls):
        cls.statistics.sort(key=lambda e: e["Test Name"])
        df = pd.DataFrame(cls.statistics, columns=cls.statistics[0].keys())
        title = f" Statistics for {cls.__class__.__name__} "
        table = df.to_markdown()
        table_width = len(table.partition("\n")[0])
        pad = table_width - len(title)
        result = (
            "\n" + "=" * (pad // 2) + title + "=" * (pad // 2 + pad % 2) + "\n" + table
        )
        logging.warning(result)
        if cls.write:
            stats_file_name = (
                os.path.commonprefix(
                    list(map(lambda e: e["Test Name"], cls.statistics))
                ).replace("::", "")
                + ".csv"
            )
            with open(Path(__file__).parent / stats_file_name, mode="w") as f:
                f.write(df.to_csv(index=False))

    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_multi_correctness(
        self, funcs: list[FunctionType], test_cases: list[Union[tuple[int, ...], int]]
    ):
        for opti_level in self.args.optimization_levels:
            ns = {}

            for func in reversed(funcs):  # First function is tested upon
                verilogified = verilogify(
                    namespace=ns, optimization_level=opti_level, mode=Modes.OVERWRITE
                )(func)

            for case in test_cases:
                case = make_tuple(case)
                verilogified(*case)

            config = CodegenConfig(random_ready=True)
            module, testbench = namespace_to_verilog(ns, config)
            if self.args.write:
                file_stem = str(
                    Path(__file__).parent
                    / (self.__dict__["_testMethodName"] + f"::O{opti_level}").replace(
                        "::", "_"
                    )
                )
                config = CodegenConfig(random_ready=False)
                namespace_to_file(file_stem, ns, config)
                context = get_context(verilogified)
                cmd = iverilog.make_cmd(
                    context.testbench_name,
                    [file_stem + ".sv", file_stem + "_tb.sv"],
                )
                logging.info(cmd)

            assert "urandom_range" in testbench
            expected = list(get_expected(verilogified))
            actual = list(
                get_actual(
                    verilogified,
                    module,
                    testbench,
                    timeout=1 + len(expected) // 64,
                )
            )
            logging.info(
                f"Actual len {len(actual)}: {str(actual[:min(len(actual), 5)])[:-1]}, ...]"
            )
            self.assertTrue(len(actual) > 0, f"{actual} {expected}")
            self.assertListEqual(actual, expected)
