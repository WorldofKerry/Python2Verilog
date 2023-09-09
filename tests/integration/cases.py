TEST_CASES = {
    "testing": [(25,), (11,)],
    "circle_lines": [(21, 37, 7), (89, 45, 43)],
    "happy_face": [(50, 51, 7), (86, 97, 43)],
    "rectangle_filled": [(32, 84, 5, 7), (64, 78, 23, 27)],
    "rectangle_lines": [(32, 84, 5, 7), (84, 96, 46, 89)],
    "fib": [(10,), (35,)],
    "dumb_loop": [(8,), (512,)],
    "floor_div": [(7,), (25,)],
    "operators": [
        (0, 0),  # warning only this one is ran with --first-test
        (0, 1),
        (1, 0),
        (1, 1),
        (0, -1),
        (-1, 0),
        (-1, -1),
        # next
        (1, 2),
        (-1, 2),
        (1, -2),
        (-1, -2),
        # next
        (2, 1),
        (-2, 1),
        (2, -1),
        (-2, -1),
    ],
}
