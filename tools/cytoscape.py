"""
Visualizes IR using Dash Cytoscape

example usage:
python3 tools/cytoscape.py tests/integration/data/integration/testing/cytoscape.log
"""

import argparse
import ast
from dash import Dash, html
import dash_cytoscape as cyto

parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawTextHelpFormatter
)
parser.add_argument("input_file", type=str, help="File containing Cytoscape elements")
args = parser.parse_args()

elements = []
with open(args.input_file) as file:
    elements = ast.literal_eval(file.read())
if not elements:
    raise RuntimeError("Empty elements")

app = Dash(__name__)

app.layout = html.Div(
    [
        cyto.Cytoscape(
            id="cytoscape-two-nodes",
            layout={"name": "cose", "nodeRepulsion": 80000},
            style={"width": "100%", "height": "800px"},
            stylesheet=[
                {
                    "selector": "edge",
                    "style": {
                        "width": 3,
                        "line-color": "#ccc",
                        "target-arrow-color": "#ccc",
                        "target-arrow-shape": "triangle",
                        "curve-style": "bezier",
                    },
                },
                {
                    "selector": "node",
                    "style": {
                        "label": "data(label)",
                        "font-size": "10",
                        "text-valign": "center",
                        "text-halign": "center",
                        "background-color": "#F0F0F0",
                        "width": "50",
                        "height": "50",
                    },
                },
            ],
            elements=elements,
        )
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
