def tree_bfs(binary_tree: list[int], queue: list[int], length: int) -> tuple[int]:
    front = 0
    rear = -1

    rear += 1
    queue[rear] = 1  # 1-based indexing in queue

    while front <= rear:
        idx = queue[front]
        front += 1

        yield (binary_tree[idx - 1],)  # convert to 0-based

        if 2 * idx < length + 1:  # account for 1-based
            rear += 1
            queue[rear] = 2 * idx
        else:
            rear = rear

        if 2 * idx + 1 < length + 1:
            rear += 1
            queue[rear] = 2 * idx + 1
        else:
            rear = rear


# binary_tree = [1, 7, 8, 2, 4, 6, 8, 6, 9]
# for elem in tree_bfs(binary_tree, [420] * len(binary_tree), len(binary_tree)):
#     print(elem)
