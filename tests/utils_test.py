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

lines1 = Lines.nestify(list_buffers)
for i, v in enumerate(lines1):
    print(i)
    print(v)
