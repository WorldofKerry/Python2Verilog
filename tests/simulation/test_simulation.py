import unittest
from pathlib import Path

from python2verilog.api import verilogify
from python2verilog.api.modes import Modes
from python2verilog.api.namespace import namespace_to_verilog, new_namespace
from python2verilog.simulation import iverilog
from python2verilog.simulation.display_parse import parse_stdout, strip_signals
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

        # @verilogify(
        #     mode=Modes.OVERWRITE,
        #     module_output="./design/func_call/dup_range.sv",
        #     testbench_output="./design/func_call/dup_range_tb.sv",
        #     optimization_level=0,
        # )
        def dup_range(base, limit, step):
            counter = base
            inst = 0  # fake generator
            while counter < limit:
                value = inst  # fake iter
                yield value
                yield value
                counter += step

        output = list(hrange(0, 10, 2))
        output = list(dup_range(0, 10, 2))
        output = list(dup_range_goal(0, 10, 2))
        print(output)

        module, testbench = namespace_to_verilog(goal_namespace)
        with temp_fifo() as module_fifo, temp_fifo() as tb_fifo:
            cmd = iverilog.make_cmd("dup_range_goal_tb", [module_fifo, tb_fifo])
            print(cmd)
            stdout, err = iverilog.run_cmd_with_fifos(
                cmd, {module_fifo: module, tb_fifo: testbench}, timeout=3
            )
            self.assertFalse(err)
            actual = list(strip_signals(parse_stdout(stdout)))
            print(actual)
            expected = list(dup_range_goal(0, 10, 2))
            self.assertListEqual(actual, expected)
