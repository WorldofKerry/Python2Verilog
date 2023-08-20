from io import StringIO
import logging
from python2verilog.api.decorator import verilogify, verilogify_function
import unittest


class TestVerilogify(unittest.TestCase):
    def test_main(self):
        namespace = {}

        module_stream = StringIO()
        testbench_stream = StringIO()

        @verilogify(
            namespace=namespace,
            write=True,
            module_output=module_stream,
            testbench_output=testbench_stream,
        )
        def count(n):
            i = 0
            while i < n:
                yield (i)
                i += 1

        count(10)

        self.assertIn(count.__name__, str(namespace[count]))

        module, testbench = verilogify_function(namespace[count])
        self.assertIn(count.__name__, testbench)
        self.assertIn(count.__name__, module)

        module_stream.seek(0)
        testbench_stream.seek(0)
        self.assertIn(count.__name__, module_stream.read())
        self.assertIn(count.__name__, testbench_stream.read())
