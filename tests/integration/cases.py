TEST_CASES = {
    "circle_lines": [(21, 37, 7), (89, 45, 43)],
    "happy_face": [(50, 51, 7), (86, 97, 43)],
    "rectangle_filled": [(32, 84, 5, 7), (64, 78, 34, 48)],
    "rectangle_lines": [(32, 84, 5, 7), (84, 96, 46, 89)],
    "fib": [(10,), (35,)],
    "testing": [(7,), (11,)],
    "dumb_loop": [(8,), (512,)],
    "floor_div": [(10,), (50,)],
    "operators": [
        (0, 7, 1, 1),
        (0, 7, -1, 1),
    ],  # weird bug with high - low > some value, presumably too many lines to display
}
