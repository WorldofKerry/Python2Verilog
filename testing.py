import matplotlib.pyplot as plt
import math


def generator_function():
    # Your generator function logic here
    for i in range(50):
        x = i
        y = math.random()
        color = math.random()
    yield x, y, color


# Collect the generated values
data = list(generator_function())

# Extract x, y, and color values
x_values = [item[0] for item in data]
y_values = [item[1] for item in data]
color_values = [item[2] for item in data]

# Normalize color values
min_color = min(color_values)
max_color = max(color_values)
normalized_colors = [
    (color - min_color) / (max_color - min_color) for color in color_values
]

# Create the scatter plot
plt.scatter(x_values, y_values, c=normalized_colors, cmap="viridis")

# Show the plot
plt.show()
