# import sys

# sys.path.append("../src/Python2Verilog/")

# import Python2Verilog

# p2v = Python2Verilog.Python2Verilog()

# print(p2v)

import os
import sys

# Get the absolute path of the parent directory of /src
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

# Add the src_path to the Python path
sys.path.append(src_path)

# Now you can import the Name module
import Python2Verilog as P2V

p2v = P2V.AstParser()

print(p2v)
