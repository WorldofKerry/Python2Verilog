import unittest
from io import StringIO

from python2verilog.api.decorators import Modes, context_to_text_and_file, verilogify


class TestVerilogify(unittest.TestCase):
    def test_main(self):
        namespace = {}

        module_stream = StringIO()
        testbench_stream = StringIO()

        @verilogify(
            namespace=namespace,
            mode=Modes.WRITE,
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

        module, testbench = context_to_text_and_file(namespace[count])
        self.assertIn(count.__name__, testbench)
        self.assertIn(count.__name__, module)

        self.assertIn(count.__name__, module_stream.read())
        self.assertIn(count.__name__, testbench_stream.read())
