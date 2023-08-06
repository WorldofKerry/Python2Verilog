from numba import njit


@njit(nogil=True)
def reallyreallycoolfunction(n: int) -> tuple[int]:
    alphaa = 0
    betaa = 123456789
    yield (betaa,)
    catt = 0
    countt = 1
    while countt < n:
        countt += 1
        alphaa = betaa + 987
        betaa = catt
        catt = alphaa + betaa + 654
        yield (catt,)


reallyreallycoolfunction(123)

# for key, value in fib.inspect_cfg().items():
# print(key, value)

# print(fib.signatures)
# fib.inspect_cfg(fib.signatures[0]).display(view=False)
# print(fib.inspect_disasm_cfg())
# print(reallyreallycoolfunction.inspect_types(pretty=False))

# GOOD: 
# for key, value in reallyreallycoolfunction.inspect_llvm().items():
#     # print(key)
#     print(type(value))
