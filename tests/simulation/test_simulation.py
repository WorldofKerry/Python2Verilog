import logging
import unittest
from pathlib import Path

from python2verilog.api import verilogify
from python2verilog.api.from_context import context_to_codegen, context_to_verilog
from python2verilog.api.modes import Modes
from python2verilog.api.namespace import namespace_to_verilog, new_namespace
from python2verilog.api.verilogify import get_actual, get_context, get_expected
from python2verilog.simulation import iverilog, parse_stdout, strip_signals
from python2verilog.utils.fifo import temp_fifo


class TestSimulation(unittest.TestCase):
    def test_all(self):
        goal_namespace = new_namespace(Path(__file__).parent / "dup_range_goal")

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

        module, testbench = namespace_to_verilog(goal_namespace)
        self.assertListEqual(
            list(get_actual(dup_range_goal, module, testbench)),
            list(get_expected(dup_range_goal)),
        )
