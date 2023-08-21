import unittest
from python2verilog.utils.env_vars import set_debug_mode, get_debug_mode


class TestEnvVars(unittest.TestCase):
    def test_env_vars(self):
        previous_mode = get_debug_mode()

        set_debug_mode(True)
        self.assertTrue(get_debug_mode())
        set_debug_mode(False)
        self.assertFalse(get_debug_mode())

        set_debug_mode(previous_mode)
        self.assertEqual(previous_mode, get_debug_mode())
