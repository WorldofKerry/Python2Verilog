def happy_face(radius) -> tuple[int, int]:
    x = 0
    y = radius
    decision = 3 - 2 * radius

    # Mid-point circle algorithm for the face
    while x <= y:
        yield x, y
        yield -x, y
        yield x, -y
        yield -x, -y
        yield y, x
        yield -y, x
        yield y, -x
        yield -y, -x

        if decision < 0:
            decision += 4 * x + 6
        else:
            decision += 4 * (x - y) + 10
            y -= 1
        x += 1

    # Filled-circle algorithm for the eyes
    eye_radius = radius // 5
    eye_x_offset = radius // 3
    eye_y_offset = radius // 3

    i = -1
    while i <= 1:
        eye_x = i * eye_x_offset
        eye_y = eye_y_offset
        decision = 3 - 2 * eye_radius

        x = 0
        y = eye_radius

        while x <= y:
            yield eye_x + x, eye_y + y
            yield eye_x - x, eye_y + y
            yield eye_x + x, eye_y - y
            yield eye_x - x, eye_y - y
            yield eye_x + y, eye_y + x
            yield eye_x - y, eye_y + x
            yield eye_x + y, eye_y - x
            yield eye_x - y, eye_y - x

            if decision < 0:
                decision += 4 * x + 6
            else:
                decision += 4 * (x - y) + 10
                y -= 1
            x += 1

        i += 2

    # Arc algorithm for the smile
    smile_radius = radius // 2
    smile_x_offset = 0
    # yield smile_radius, 991 # for debugging
    smile_y_offset = -smile_radius // 2
    # yield smile_y_offset, 994

    x = 0
    y = smile_radius
    decision = 3 - 2 * smile_radius

    while x <= y:
        # yield x, 992
        # yield y, 993
        yield smile_x_offset + x, smile_y_offset + y
        yield smile_x_offset - x, smile_y_offset + y

        if decision < 0:
            decision += 4 * x + 6
        else:
            decision += 4 * (x - y) + 10
            y -= 1
        x += 1
