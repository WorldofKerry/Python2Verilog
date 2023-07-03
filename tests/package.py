import os
import sys

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(src_path)

import python2verilog

__all__ = ["python2verilog"]
