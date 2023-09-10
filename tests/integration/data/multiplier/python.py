def multiplier(multiplicand, multiplier) -> tuple[int]:
    product = 0
    count = 0
    while count < multiplier:
        product += multiplicand
        count += 1
    yield product
