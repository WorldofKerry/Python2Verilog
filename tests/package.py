import os
import sys

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.append(src_path)

import Python2Verilog

__all__ = ["Python2Verilog"]
