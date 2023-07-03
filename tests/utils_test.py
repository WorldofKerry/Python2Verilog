import os
import sys

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(src_path)

from python2verilog import Lines, NestedLines

sb0 = Lines(["a", "b"])
# print(sb0)

list_buffers = [
    [Lines(["a0", "b0"]), Lines(["c0", "d0"])],
    [Lines(["a1", "b1"]), Lines(["c1", "d1"])],
    [Lines(["a2", "b2"]), Lines(["c2", "d2"])],
]

# print(StringBuffer.do_list(0, list_buffers))
# print(list_buffers)

lb0 = NestedLines(list_buffers)
print(lb0)

lb0 + (Lines(["a3", "b3"]), Lines(["c3", "d3"]))
print(lb0)