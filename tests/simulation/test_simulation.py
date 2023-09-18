import logging
import unittest
from pathlib import Path

import pytest

from python2verilog.api import verilogify
from python2verilog.api.from_context import (
    context_to_codegen,
    context_to_verilog,
    context_to_verilog_and_dump,
)
from python2verilog.api.modes import Modes
from python2verilog.api.namespace import (
    namespace_to_file,
    namespace_to_verilog,
    new_namespace,
)
from python2verilog.api.verilogify import get_actual, get_context, get_expected
from python2verilog.simulation import iverilog, parse_stdout, strip_signals
from python2verilog.utils.fifo import temp_fifo


@pytest.mark.usefixtures("argparse")
class TestSimulation(unittest.TestCase):
    def test_o0(self):
        ns = {}

        @verilogify(
            mode=Modes.OVERWRITE,
            namespace=ns,
        )
        def hrange(n):
            i = 0
            while i < n:
                yield i, i
                i += 1

        @verilogify(
            mode=Modes.OVERWRITE,
            namespace=ns,
            optimization_level=0,
        )
        def dup_range_goal(n):
            inst = hrange(n)
            for i, j in inst:
                yield i

        list(dup_range_goal(10))

        module, testbench = namespace_to_verilog(ns)
        with open(Path(__file__).parent / "o0.sv", mode="w") as f:
            f.write(str(module))
        with open(Path(__file__).parent / "o0_tb.sv", mode="w") as f:
            f.write(str(testbench))
        self.assertListEqual(
            list(get_actual(dup_range_goal, module, testbench, timeout=1)),
            list(get_expected(dup_range_goal)),
        )

    def test_triple0(self):
        """
        Circle lines with -O0
        """
        ns = {}

        @verilogify(namespace=ns, mode=Modes.OVERWRITE, optimization_level=0)
        def circle_lines(s_x, s_y, height) -> tuple[int, int, int, int, int, int]:
            x = 0
            y = height
            d = 3 - 2 * y
            yield (s_x + x, s_y + y)
            yield (s_x + x, s_y - y)
            yield (s_x - x, s_y + y)
            yield (s_x - x, s_y - y)
            yield (s_x + y, s_y + x)
            yield (s_x + y, s_y - x)
            yield (s_x - y, s_y + x)
            yield (s_x - y, s_y - x)
            while y >= x:
                x = x + 1
                if d > 0:
                    y = y - 1
                    d = d + 4 * (x - y) + 10
                else:
                    d = d + 4 * x + 6
                yield (s_x + x, s_y + y)
                yield (s_x + x, s_y - y)
                yield (s_x - x, s_y + y)
                yield (s_x - x, s_y - y)
                yield (s_x + y, s_y + x)
                yield (s_x + y, s_y - x)
                yield (s_x - y, s_y + x)
                yield (s_x - y, s_y - x)

        @verilogify(namespace=ns, mode=Modes.OVERWRITE, optimization_level=0)
        def triple_circle(centre_x, centre_y, radius):
            # noqa
            c_x = centre_x
            c_y = centre_y
            c_x1 = c_x + radius // 2
            c_y1 = c_y + radius * 2 // 6
            c_x2 = c_x - radius // 2
            c_y2 = c_y + radius * 2 // 6
            c_x3 = c_x
            c_y3 = c_y - radius * 2 // 6

            gen0 = circle_lines(c_x1, c_y1, radius)
            for x, y in gen0:
                yield x, y
            gen1 = circle_lines(c_x2, c_y2, radius)
            for x, y in gen1:
                yield x, y
            # reuse
            gen0 = circle_lines(c_x3, c_y3, radius)
            for x, y in gen0:
                yield x, y

        triple_circle(50, 50, 8)

        module, testbench = namespace_to_verilog(ns)
        self.assertListEqual(
            list(get_actual(triple_circle, module, testbench, timeout=1)),
            list(get_expected(triple_circle)),
        )

    def test_triple(self):
        ns = new_namespace(Path(__file__).parent / "new_namespace")

        @verilogify(namespace=ns, mode=Modes.OVERWRITE)
        def circle_lines(s_x, s_y, height) -> tuple[int, int, int, int, int, int]:
            x = 0
            y = height
            d = 3 - 2 * y
            yield (s_x + x, s_y + y)
            yield (s_x + x, s_y - y)
            yield (s_x - x, s_y + y)
            yield (s_x - x, s_y - y)
            yield (s_x + y, s_y + x)
            yield (s_x + y, s_y - x)
            yield (s_x - y, s_y + x)
            yield (s_x - y, s_y - x)
            while y >= x:
                x = x + 1
                if d > 0:
                    y = y - 1
                    d = d + 4 * (x - y) + 10
                else:
                    d = d + 4 * x + 6
                yield (s_x + x, s_y + y)
                yield (s_x + x, s_y - y)
                yield (s_x - x, s_y + y)
                yield (s_x - x, s_y - y)
                yield (s_x + y, s_y + x)
                yield (s_x + y, s_y - x)
                yield (s_x - y, s_y + x)
                yield (s_x - y, s_y - x)

        @verilogify(namespace=ns, mode=Modes.OVERWRITE, optimization_level=0)
        def triple_circle(centre_x, centre_y, radius):
            # noqa
            c_x = centre_x
            c_y = centre_y
            c_x1 = c_x + radius // 2
            c_y1 = c_y + radius * 2 // 6
            c_x2 = c_x - radius // 2
            c_y2 = c_y + radius * 2 // 6
            c_x3 = c_x
            c_y3 = c_y - radius * 2 // 6

            gen0 = circle_lines(c_x1, c_y1, radius)
            for x, y in gen0:
                yield x, y
            gen1 = circle_lines(c_x2, c_y2, radius)
            for x, y in gen1:
                yield x, y
            # reuse
            gen0 = circle_lines(c_x3, c_y3, radius)
            for x, y in gen0:
                yield x, y

        triple_circle(50, 50, 8)

        # with open("./cyto.log", mode="w") as f:
        #     _, _, cy = context_to_verilog_and_dump(get_context(triple_circle))
        #     f.write(str(cy))
        module, testbench = namespace_to_verilog(ns)
        self.assertListEqual(
            list(get_actual(triple_circle, module, testbench, timeout=1)),
            list(get_expected(triple_circle)),
        )
        with open(Path(__file__).parent / "triple_o1.sv", mode="w") as f:
            f.write(str(module))
        with open(Path(__file__).parent / "triple_o1_tb.sv", mode="w") as f:
            f.write(str(testbench))
