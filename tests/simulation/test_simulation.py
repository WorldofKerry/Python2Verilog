import logging
import unittest
from pathlib import Path

from python2verilog.api import verilogify
from python2verilog.api.modes import Modes
from python2verilog.api.namespace import namespace_to_verilog, new_namespace
from python2verilog.api.verilogify import get_context
from python2verilog.simulation import iverilog, parse_stdout, strip_signals
from python2verilog.utils.fifo import temp_fifo

goal_namespace = new_namespace(Path(__file__).parent / "dup_range_goal")


class TestSimulation(unittest.TestCase):
    def test_all(self):
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

        output = list(hrange(1, 11, 3))
        output = list(dup_range_goal(0, 10, 2))
        print(output)

        module, testbench = namespace_to_verilog(goal_namespace)
        with temp_fifo() as module_fifo, temp_fifo() as tb_fifo:
            stdout, err = iverilog.run_with_fifos(
                "dup_range_goal_tb",
                {module_fifo: module, tb_fifo: testbench},
                timeout=3,
            )
            self.assertFalse(err)
            logging.warning(stdout)
            actual = list(strip_signals(parse_stdout(stdout)))
            expected = []
            test_cases = list(get_context(dup_range_goal).test_cases)
            for test in test_cases:
                expected += list(dup_range_goal(*test))
            print("test cases", goal_namespace[dup_range_goal.__name__].test_cases)
            self.assertListEqual(actual, expected)
