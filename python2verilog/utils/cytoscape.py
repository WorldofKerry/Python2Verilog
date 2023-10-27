"""
Visualizes IR using Dash Cytoscape

example usage:
python3 tools/cytoscape.py tests/integration/data/integration/testing/cytoscape.log
"""


import argparse
import ast

import dash_cytoscape as cyto  # type: ignore # pylint: disable=import-error
from dash import Dash, html  # type: ignore # pylint: disable=import-error


def main():
    """
    Main
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_file", type=str, help="File containing Cytoscape elements"
    )
    args = parser.parse_args()

    elements = []
    with open(args.input_file, encoding="utf8") as file:
        elements = ast.literal_eval(file.read())
    if not elements:
        raise RuntimeError("Empty elements")

    app = Dash(__name__)

    cytoscape = cyto.Cytoscape(
        id="cytoscape-two-nodes",
        layout={"name": "cose", "nodeRepulsion": 80000},
        style={"width": "100%", "height": "1920px"},
        stylesheet=[
            {
                "selector": "edge",
                "style": {
                    "width": 20,
                    "line-color": "#303030",
                    "target-arrow-color": "#303030",
                    "target-arrow-shape": "triangle",
                    "curve-style": "bezier",
                    "label": "data(label)",
                    "font-size": "5",
                },
            },
            {
                "selector": "node",
                "style": {
                    "label": "data(label)",
                    "font-size": "10",
                    "text-valign": "center",
                    "text-halign": "center",
                    "background-color": "#101010",
                    "color": "#FFFFFF",
                    "width": "100",
                    "height": "100",
                    "text-wrap": "wrap",
                },
            },
            {
                "selector": "edge[class = 'ClockedEdge']",
                "style": {
                    "line-color": "#FF6666",
                },
            },
            {
                "selector": "edge[class = 'NonClockedEdge']",
                "style": {
                    "line-color": "#66FF66",
                },
            },
            {
                "selector": "edge[class = 'ControlFlow']",
                "style": {
                    "line-color": "#00FAB6",
                },
            },
            {
                "selector": "edge[class = 'DataFlow']",
                "style": {
                    "line-color": "#FAB900",
                },
            },
            {
                "selector": "edge[class = 'Mapper']",
                "style": {
                    "line-color": "#DC01FA",
                },
            },
        ],
        elements=elements,
    )

    app.layout = html.Div([cytoscape])
    app.run(debug=True)


if __name__ == "__main__":
    main()
