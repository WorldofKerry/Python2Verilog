from python2verilog import verilogify


@verilogify
def get_data(addr):
    """
    Dummy function
    """
    print(addr)
    # # Testing reg func that takes more than one clock cycle
    # i = 0
    # while i < addr:
    #     i += 1
    # return i
    return addr + 42069


@verilogify
def read32to8(base, count):
    """ """
    i = 0
    while i < count:
        data = get_data(base + count * 4)
        j = 0
        while j < 4:
            yield data


read32to8(256, 2)
