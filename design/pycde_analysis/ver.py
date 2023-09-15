import sys

from pycde import Input, Module, Output, System, dim, generator, types


class WireNames(Module):
    clk = Input(types.i1)
    data_in = Input(dim(32, 3))
    sel = Input(types.i2)

    a = Output(types.i32)
    b = Output(types.i32)

    @generator
    def build(self):
        foo = self.data_in[0]
        foo.name = "foo"
        arr_data = dim(32, 4)([1, 2, 3, 4], "arr_data")
        self.a = foo.reg(self.clk).reg(self.clk)
        self.b = arr_data[self.sel]


sys = System([WireNames], output_directory=sys.argv[1])
sys.generate()
sys.run_passes()
sys.print()
