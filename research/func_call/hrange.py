from python2verilog import verilogify


@verilogify(write=True, overwrite=True)
def hrange(base, limit, step):
    i = base
    while i < limit:
        yield i
        i += step


output = list(hrange(0, 10, 2))
print(output)
