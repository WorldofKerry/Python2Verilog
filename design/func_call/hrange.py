import sys
from pathlib import Path

P2V_PATH = Path(__file__).parent.absolute().resolve().parent.parent
sys.path.insert(0, str(P2V_PATH))

from python2verilog import Modes, verilogify


@verilogify(mode=Modes.OVERWRITE)
def hrange(base, limit, step):
    i = base
    while i < limit:
        yield i
        i += step


@verilogify(
    mode=Modes.OVERWRITE,
    module_output="./design/func_call/dup_range_goal.sv",
    testbench_output="./design/func_call/dup_range_goal_tb.sv",
    optimization_level=1,
)
def dup_range_goal(base, limit, step):
    inst = hrange(base, limit, step)
    for i in inst:
        yield i
        yield i


# @verilogify(
#     mode=Modes.OVERWRITE,
#     module_output="./design/func_call/dup_range.sv",
#     testbench_output="./design/func_call/dup_range_tb.sv",
#     optimization_level=0,
# )
def dup_range(base, limit, step):
    counter = base
    inst = 0  # fake generator
    while counter < limit:
        value = inst  # fake iter
        yield value
        yield value
        counter += step


output = list(hrange(0, 10, 2))
output = list(dup_range(0, 10, 2))
output = list(dup_range_goal(0, 10, 2))
print(output)
