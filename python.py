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

# print(reallyreallycoolfunction.signatures)
print(type(reallyreallycoolfunction.overloads[reallyreallycoolfunction.signatures[0]]))
print(
    type(
        reallyreallycoolfunction.overloads[
            reallyreallycoolfunction.signatures[0]
        ].library
    )
)
print(
    type(
        reallyreallycoolfunction.overloads[
            reallyreallycoolfunction.signatures[0]
        ].library._final_module
    )
)
# for func in reallyreallycoolfunction.overloads[
#     reallyreallycoolfunction.signatures[0]
# ].library._final_module.functions:
#     name = func.name
#     print(func.name + "\n")
    
# print("\n\n")

for func in reallyreallycoolfunction.overloads[
    reallyreallycoolfunction.signatures[0]
].library._final_module.functions:
    name = func.name
    if (True 
        and "__main__" in name 
        and "finalize_" not in name 
        and "cpython" not in name
        and "next" in name
        ):
        
        print(func.name + "\n")
        break

print(type(reallyreallycoolfunction.overloads[
    reallyreallycoolfunction.signatures[0]
].library._final_module.get_function(name)))




# print("\n\n\n")
# print(
#     str(
#         reallyreallycoolfunction.overloads[
#             reallyreallycoolfunction.signatures[0]
#         ].library._final_module
#     )
# )

# print(str(reallyreallycoolfunction.overloads[reallyreallycoolfunction.signatures[0]].library._final_module.get_function("_ZN8__main__24reallyreallycoolfunction4nextE168UniTuple_28int64_20x_201_29_20generator_28func_3d_3cfunction_20reallyreallycoolfunction_20at_200x7f78e703eb90_3e_2c_20args_3d_28int64_2c_29_2c_20has_finalizer_3dTrue_29c600f0

"""
_ZN8__main__24reallyreallycoolfunction4nextE168UniTuple_28int64_20x_201_29_20generator_28func_3d_3cfunction_20reallyreallycoolfunction_20at_200x7fe0aa6cab90_3e_2c_20args_3d_28int64_2c_29_2c_20has_finalizer_3dTrue_29

_ZN8__main__24reallyreallycoolfunction4nextE168UniTuple_28int64_20x_201_29_20generator_28func_3d_3cfunction_20reallyreallycoolfunction_20at_200x7f3df9112b90_3e_2c_20args_3d_28int64_2c_29_2c_20has_finalizer_3dTrue_29
"""
