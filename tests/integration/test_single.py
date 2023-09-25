import inspect
import logging
import re
import subprocess
import warnings
from pathlib import Path
from types import FunctionType
from typing import Union
from unittest import TestCase

import pandas as pd
import pytest
from parameterized import parameterized

from python2verilog import (
    Modes,
    get_actual,
    get_context,
    get_expected,
    namespace_to_file,
    namespace_to_verilog,
    verilogify,
)
from python2verilog.backend.verilog.config import CodegenConfig
from python2verilog.simulation import iverilog

from .functions import *
from .utils import make_tuple, name_func

PARAMETERS = [
    (fib, [(10)]),
    (floor_div, [(13)]),
    (operators, [(13, 17)]),
    (multiplier, [(13, 17)]),
    (division, [(6, 7, 10), (2, 3, 10)]),
    (circle_lines, [(10, 10, 4), (13, 13, 7)]),
    (happy_face, [(10, 10, 4), (13, 13, 7)]),
    (rectangle_filled, [(10, 10, 4, 5), (13, 13, 7, 11)]),
    (rectangle_lines, [(10, 10, 4, 5), (13, 13, 7, 11)]),
]


@pytest.mark.usefixtures("argparse")
class TestComplete(TestCase):
    statistics: list[dict] = []

    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_single_performance(
        self, func: FunctionType, test_cases: list[Union[tuple[int, ...], int]]
    ):
        for opti_level in self.args.optimization_levels:
            ns = {}
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
                file_stem = test_name.replace("::", "_")
                namespace_to_file(file_stem, ns, config)
                context = get_context(verilogified)
                cmd = iverilog.make_cmd(
                    context.testbench_name,
                    [file_stem + ".sv", file_stem + "_tb.sv"],
                )
                logging.info(cmd)

            expected = list(get_expected(verilogified))
            actual = list(
                get_actual(
                    verilogified, module, testbench, timeout=1 + len(expected) // 64
                )
            )
            logging.info(
                f"Actual len {len(actual)}: {str(actual[:min(len(actual), 5)])[:-1]}, ...]"
            )
            self.assertTrue(len(actual) > 0)
            self.assertListEqual(actual, expected)

            statistics = {
                "Test Name": test_name.split("/")[-1],
                "Py Yields": len(expected),
                "Ver Clks": len(
                    list(
                        get_actual(
                            verilogified,
                            module,
                            testbench,
                            timeout=1 + len(expected) // 64,
                            include_invalid=True,
                        )
                    )
                ),
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

    @parameterized.expand(
        input=PARAMETERS,
        name_func=name_func,
    )
    def test_single_correctness(
        self, func: FunctionType, test_cases: list[Union[tuple[int, ...], int]]
    ):
        for opti_level in self.args.optimization_levels:
            ns = {}
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
                module, testbench, namespace_to_file(file_stem, ns, config)
                context = get_context(verilogified)
                cmd = iverilog.make_cmd(
                    context.testbench_name,
                    [file_stem + ".sv", file_stem + "_tb.sv"],
                )
                logging.info(cmd)

            expected = list(get_expected(verilogified))
            assert "urandom_range" in testbench
            actual = list(
                get_actual(
                    verilogified, module, testbench, timeout=1 + len(expected) // 64
                )
            )
            logging.info(
                f"Actual len {len(actual)}: {str(actual[:min(len(actual), 5)])[:-1]}, ...]"
            )
            self.assertTrue(len(actual) > 0)
            self.assertListEqual(actual, expected)
