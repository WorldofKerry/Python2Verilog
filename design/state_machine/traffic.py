import random


class State:
    NORTH_SOUTH = 0
    EAST_WEST = 1


def traffic_handler(initial: State = State.NORTH_SOUTH):
    state = initial
    ns = 0
    ew = 0
    while True:
        print(f"ns {ns}, ew {ew}")
        if state == State.NORTH_SOUTH:
            output = State.NORTH_SOUTH
        else:
            output = State.EAST_WEST
        ns_poll, ew_poll = yield output
        ns += ns_poll
        ew += ew_poll
        if ns > ew:
            state = State.NORTH_SOUTH
        else:
            state = State.EAST_WEST


fsm = traffic_handler()
next(fsm)
for _ in range(10):
    rand = lambda: random.randint(-5, 5)
    a, b = rand(), rand()
    print(f"a {a}, b {b}, {fsm.send((a, b))}")
