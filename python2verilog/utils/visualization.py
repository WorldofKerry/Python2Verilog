"""
Visualization Tools
"""

import logging
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt  # type: ignore
import numpy as np


def make_visual(generator_inst, directory: Optional[str] = None):
    """
    Any iterable of tuples where the tuples are of length > 0 will work.
    Visualizes the first 3 elements of each tuple as (x, y, colour)
    """

    # Generate the data using the generator function
    data_triple_list = []

    for idx, yields in enumerate(generator_inst):
        if isinstance(yields, int):
            yields = (yields,)
        if len(yields) >= 3:
            data_triple_list.append(yields[:3])
        elif len(yields) >= 2:
            data_triple_list.append((*yields[:2], idx))
        else:
            data_triple_list.append((yields[0], idx, 0))
        if idx > 1000:
            break

    data_triple = np.array(data_triple_list)

    try:
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
        plt.title("Colorbar Plot")

        # Add color bar
        cdict = {
            "red": (
                (0.0, 0.0, 0.0),
                (0.1, 0.5, 0.5),
                (0.2, 0.0, 0.0),
                (0.4, 0.2, 0.2),
                (0.6, 0.0, 0.0),
                (0.8, 1.0, 1.0),
                (1.0, 1.0, 1.0),
            ),
            "green": (
                (0.0, 0.0, 0.0),
                (0.1, 0.0, 0.0),
                (0.2, 0.0, 0.0),
                (0.4, 1.0, 1.0),
                (0.6, 1.0, 1.0),
                (0.8, 1.0, 1.0),
                (1.0, 0.0, 0.0),
            ),
            "blue": (
                (0.0, 0.0, 0.0),
                (0.1, 0.5, 0.5),
                (0.2, 1.0, 1.0),
                (0.4, 1.0, 1.0),
                (0.6, 0.0, 0.0),
                (0.8, 0.0, 0.0),
                (1.0, 0.0, 0.0),
            ),
        }

        plt.pcolor(
            grid,
            cmap=matplotlib.colors.LinearSegmentedColormap(
                "my_colormap", cdict, 256  # type: ignore
            ),
        )
        cbar = plt.colorbar()
        cbar.set_label("Z")

        plt.gca().invert_yaxis()

        # Show the plot
        plt.show()
        if directory:
            plt.savefig(directory)

        plt.clf()
        plt.cla()
        plt.close()
    except IndexError as e:
        logging.info(
            f"Skipping make_visual for {str(generator_inst)} due to negative outputs {e}"
        )
