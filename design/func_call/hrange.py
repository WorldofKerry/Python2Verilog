import sys
from pathlib import Path

P2V_PATH = Path(__file__).parent.absolute().resolve().parent.parent
sys.path.insert(0, str(P2V_PATH))

from python2verilog import Modes, verilogify
from python2verilog.api.namespace import new_namespace

goal_namespace = new_namespace(Path(__file__).parent / "dup_range_goal")


@verilogify(
    mode=Modes.OVERWRITE,
    namespace=goal_namespace,
)
def hrange(base, limit, step):
    i = base
    while i < limit:
        yield i, i
        i += step


@verilogify(
    mode=Modes.OVERWRITE,
    namespace=goal_namespace,
    optimization_level=1,
)
def dup_range_goal(base, limit, step):
    inst = hrange(base, limit, step)
    for i, j in inst:
        yield i
        yield j


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
