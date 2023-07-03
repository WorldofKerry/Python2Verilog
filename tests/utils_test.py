import os
import sys

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(src_path)

from python2verilog import StringBuffer, ListBuffer

sb0 = StringBuffer(["a", "b"])
# print(sb0)

list_buffers = [
    [StringBuffer(["a0", "b0"]), StringBuffer(["c0", "d0"])],
    [StringBuffer(["a1", "b1"]), StringBuffer(["c1", "d1"])],
    [StringBuffer(["a2", "b2"]), StringBuffer(["c2", "d2"])],
]

# print(StringBuffer.do_list(0, list_buffers))
# print(list_buffers)

lb0 = ListBuffer(list_buffers)
print(lb0)

lb0 + (StringBuffer(["a3", "b3"]), StringBuffer(["c3", "d3"]))
print(lb0)