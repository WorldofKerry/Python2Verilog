import logging
from python2verilog.api.decorator import verilogify
import unittest


class TestVerilogify(unittest.TestCase):
    def test_main(self):
        namespace = {}

        @verilogify(namespace=namespace)
        def count(n):
            i = 0
            while i < n:
                yield (i)
                i += 1

        count(10)

        logging.error(namespace[count])
