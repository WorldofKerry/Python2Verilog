"""Visualization Tools"""

import numpy as np
import matplotlib.pyplot as plt


def make_visual(generator_inst, directory: str):
    """
    Any iterable of tuples where the tuples are of length > 0 will work.
    Visualizes the first 3 elements of each tuple as (x, y, colour)
    """

    # Generate the data using the generator function
    data_triple_list = []

    for idx, yields in enumerate(generator_inst):
        if len(yields) >= 3:
            data_triple_list.append(yields[:3])
        elif len(yields) >= 2:
            data_triple_list.append((*yields[:2], 1))
        else:
            data_triple_list.append((yields[0], idx, 1))

    data_triple = np.array(data_triple_list)

    height = max(data_triple[:, 0])
    width = max(data_triple[:, 1])
    grid = np.zeros((int(height) + 1, int(width) + 1))
    for x_coord, y_coord, colour in data_triple:
        grid[x_coord, y_coord] = colour

    # Create the pixel-like plot
    plt.imshow(grid)

    # Set labels and title
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.title("Pixel-like Plot")

    # Add color bar
    cbar = plt.colorbar()
    cbar.set_label("Z")

    plt.gca().invert_yaxis()

    # Show the plot
    # plt.show()
    plt.savefig(directory)

    plt.clf()
    plt.cla()
