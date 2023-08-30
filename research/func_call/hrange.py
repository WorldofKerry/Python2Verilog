import sys
from pathlib import Path

P2V_PATH = Path(__file__).parent.absolute().resolve().parent.parent
sys.path.insert(0, str(P2V_PATH))

from python2verilog import verilogify


@verilogify(write=True, overwrite=True, optimization_level=1)
def hrange(base, limit, step):
    i = base
    while i < limit:
        yield i
        i += step


output = list(hrange(0, 10, 2))
print(output)
