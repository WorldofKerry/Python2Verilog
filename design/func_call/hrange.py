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


# @verilogify(write=True, overwrite=True, optimization_level=1)
def dup_range(base, limit, step):
    for i in hrange(base, limit, step):
        yield i
        yield i


output = list(dup_range(0, 10, 2))
print(output)
