from python2verilog.backend.ast import NonBlockingSubsitution, BlockingSubsitution
import unittest
import warnings


class TestAST(unittest.TestCase):
    def test_nonblocking(self):
        nb = NonBlockingSubsitution("a", "b")
        self.assertEqual(nb.to_string(), "a <= b;")

        b = BlockingSubsitution("c", "d")
        self.assertEqual(b.to_string(), "c = d;")
