import logging
import unittest
from pathlib import Path

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


class TestSimulation(unittest.TestCase):
    def test_o0(self):
        goal_namespace = new_namespace(Path(__file__).parent / "o0")

        @verilogify(
            mode=Modes.OVERWRITE,
            namespace=goal_namespace,
        )
        def hrange(base, limit, step):
            i = base
            while i < limit:
                yield i, i
                i += step

        @verilogify(
            mode=Modes.OVERWRITE,
            namespace=goal_namespace,
            optimization_level=0,
        )
        def dup_range_goal(base, limit, step):
            inst = hrange(base, limit, step)
            for i, j in inst:
                if i > 4:
                    yield i
                yield j

        list(hrange(1, 11, 3))
        list(dup_range_goal(0, 10, 2))

        # with open("./cyto.log", mode="w") as f:
        #     _, _, cy = context_to_verilog_and_dump(get_context(dup_range_goal))
        #     f.write(str(cy))
        module, testbench = namespace_to_verilog(goal_namespace)
        self.assertListEqual(
            list(get_actual(dup_range_goal, module, testbench, timeout=1)),
            list(get_expected(dup_range_goal)),
        )

    def test_o1(self):
        goal_namespace = new_namespace(Path(__file__).parent / "o1")

        @verilogify(
            mode=Modes.OVERWRITE,
            namespace=goal_namespace,
        )
        def hrange(base, limit, step):
            i = base
            while i < limit:
                yield i, i
                i += step

        @verilogify(
            mode=Modes.OVERWRITE,
            namespace=goal_namespace,
            optimization_level=1,
        )
        def dup_range_goal(base, limit, step):
            inst = hrange(base, limit, step)
            for i, j in inst:
                if i > 4:
                    yield i
                yield j

        list(hrange(1, 11, 3))
        list(dup_range_goal(0, 10, 2))

        with open("./cyto.log", mode="w") as f:
            _, _, cy = context_to_verilog_and_dump(get_context(dup_range_goal))
            f.write(str(cy))
        module, testbench = namespace_to_verilog(goal_namespace)
        # self.assertListEqual(
        #     list(get_actual(dup_range_goal, module, testbench, timeout=1)),
        #     list(get_expected(dup_range_goal)),
        # )

    def test_triple(self):
        goal_namespace = new_namespace(Path(__file__).parent / "triple_o1")

        @verilogify(namespace=goal_namespace, mode=Modes.OVERWRITE)
        def circle_lines(s_x, s_y, height) -> tuple[int, int, int, int, int, int]:
            x = 0
            y = height
            d = 3 - 2 * y
            yield (s_x + x, s_y + y, height, x, y, d)
            yield (s_x + x, s_y - y, height, x, y, d)
            yield (s_x - x, s_y + y, height, x, y, d)
            yield (s_x - x, s_y - y, height, x, y, d)
            yield (s_x + y, s_y + x, height, x, y, d)
            yield (s_x + y, s_y - x, height, x, y, d)
            yield (s_x - y, s_y + x, height, x, y, d)
            yield (s_x - y, s_y - x, height, x, y, d)
            while y >= x:
                x = x + 1
                if d > 0:
                    y = y - 1
                    d = d + 4 * (x - y) + 10
                else:
                    d = d + 4 * x + 6
                yield (s_x + x, s_y + y, height, x, y, d)
                yield (s_x + x, s_y - y, height, x, y, d)
                yield (s_x - x, s_y + y, height, x, y, d)
                yield (s_x - x, s_y - y, height, x, y, d)
                yield (s_x + y, s_y + x, height, x, y, d)
                yield (s_x + y, s_y - x, height, x, y, d)
                yield (s_x - y, s_y + x, height, x, y, d)
                yield (s_x - y, s_y - x, height, x, y, d)

        @verilogify(
            namespace=goal_namespace, mode=Modes.OVERWRITE, optimization_level=0
        )
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
            for x, y, a, b, c, d in gen0:
                yield x, y
            # gen1 = circle_lines(c_x2, c_y2, radius)
            # for x, y, a, b, c, d in gen1:
            #     yield x, y
            # gen2 = circle_lines(c_x3, c_y3, radius)
            # for x, y, a, b, c, d in gen2:
            #     yield x, y

        triple_circle(50, 50, 8)

        with open("./cyto.log", mode="w") as f:
            _, _, cy = context_to_verilog_and_dump(get_context(triple_circle))
            f.write(str(cy))
        module, testbench = namespace_to_verilog(goal_namespace)
        # self.assertListEqual(
        #     list(get_actual(triple_circle, module, testbench, timeout=1)),
        #     list(get_expected(triple_circle)),
        # )
