from io import StringIO

import numba


@numba.njit
def circle_lines(centre_x, centre_y, radius):
    offset_y = 0
    offset_x = radius
    crit = 1 - radius
    while offset_y <= offset_x:
        yield (centre_x + offset_x, centre_y + offset_y)  # -- octant 1
        yield (centre_x + offset_y, centre_y + offset_x)  # -- octant 2
        yield (centre_x - offset_x, centre_y + offset_y)  # -- octant 4
        yield (centre_x - offset_y, centre_y + offset_x)  # -- octant 3
        yield (centre_x - offset_x, centre_y - offset_y)  # -- octant 5
        yield (centre_x - offset_y, centre_y - offset_x)  # -- octant 6
        yield (centre_x + offset_x, centre_y - offset_y)  # -- octant 8
        yield (centre_x + offset_y, centre_y - offset_x)  # -- octant 7
        offset_y = offset_y + 1
        if crit <= 0:
            crit = crit + 2 * offset_y + 1
        else:
            offset_x = offset_x - 1
            crit = crit + 2 * (offset_y - offset_x) + 1


@numba.njit
def olympic_logo_mids(mid_x, mid_y, spread):
    """
    Yields the middle coordinates and the color
    for the 5 circles in the olympics logo
    """
    yield mid_x, mid_y + spread, 50
    yield mid_x + spread * 2, mid_y + spread, 180
    yield mid_x - spread * 2, mid_y + spread, 500
    yield mid_x + spread, mid_y - spread, 400
    yield mid_x - spread, mid_y - spread, 300


@numba.njit
def olympic_logo(mid_x, mid_y, radius):
    """
    Draws the olympic logo
    """
    spread = radius - 2
    middles_and_colors = olympic_logo_mids(mid_x, mid_y, spread)
    for x, y, color in middles_and_colors:
        coords = circle_lines(x, y, radius)
        for x, y in coords:
            yield x, y, color


olympic_logo(20, 25, 7)

# print(olympic_logo.__dict__.keys())
# print(olympic_logo.typingctx.__dict__.keys())
# print(olympic_logo.typingctx._functions.__dict__.keys())

file = StringIO()
# numba.jit(nopython=True)(olympic_logo).inspect_types()
# print(result.inspect_cfg(result.signatures[0]).display(view=True))
# result.inspect_cfg(file=file)
# result.inspect_types(file=file)
# print(olympic_logo.inspect_cfg(olympic_logo.signatures[0]).display(view=True))
# print(dir(olympic_logo))
overload = list(olympic_logo.overloads.items())[0][
    1
]  # first overload -> value of key-item pair
print(overload.type_annotation)
print(dir(overload.type_annotation))
annotation = overload.type_annotation
print()
data = list(
    annotation.prepare_annotations().values()
)  # corresponds to each line of source code
for block in data:
    for line in block:
        print(line)
        print(type(line))
# for sig in olympic_logo.signatures:
#     print(sig.__dict__)

file.seek(0)
print(file.read())

# result = numba.jit('c16(f8)', nopython=True)(olympic_logo)
# for _, defn in result.overloads.items():
#     temp = StringIO()
#     print(defn.__dict__)
#     # defn.inspect_types(temp)
#     # print(temp)
