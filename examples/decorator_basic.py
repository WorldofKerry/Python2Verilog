from python2verilog.api import Modes, verilogify


@verilogify(mode=Modes.OVERWRITE)
def fib(n):
    a = 0
    b = 1
    c = 0
    count = 1
    while count < n:
        count += 1
        a = b
        b = c
        c = a + b
        yield c


for i in range(10):
    fib(i)
