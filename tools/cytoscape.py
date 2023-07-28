from dash import Dash, html
import dash_cytoscape as cyto

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
                        "background-color": "#FFFFFF",
                    },
                },
            ],
            elements=[
                {"data": {"id": "_3", "label": "i <= 0"}},
                {"data": {"source": "_3", "target": "_3_e_o15"}},
                {"data": {"id": "_3_e_o15", "label": "Next, nonclocked"}},
                {"data": {"source": "_3_e_o15", "target": "_2_o2"}},
                {"data": {"id": "_2_o2", "label": "a <= 0"}},
                {"data": {"source": "_2_o2", "target": "_2_e_o14"}},
                {"data": {"id": "_2_e_o14", "label": "Next, nonclocked"}},
                {"data": {"source": "_2_e_o14", "target": "_1_while_o13"}},
                {"data": {"id": "_1_while_o13", "label": "if ((0 < n))"}},
                {"data": {"source": "_1_while_o13", "target": "_1_edge_o11"}},
                {"data": {"source": "_1_while_o13", "target": "_1_f_o12"}},
                {"data": {"id": "_1_edge_o11", "label": "True, nonclocked"}},
                {"data": {"source": "_1_edge_o11", "target": "_1_while_1_o3"}},
                {"data": {"id": "_1_while_1_o3", "label": "i <= (0 + 1)"}},
                {"data": {"source": "_1_while_1_o3", "target": "_1_while_1_e_o10"}},
                {"data": {"id": "_1_while_1_e_o10", "label": "Next, nonclocked"}},
                {"data": {"source": "_1_while_1_e_o10", "target": "_1_while_0_o4"}},
                {"data": {"id": "_1_while_0_o4", "label": "a <= ((0 + 1) + 1)"}},
                {"data": {"source": "_1_while_0_o4", "target": "_1_while_0_e_o9"}},
                {"data": {"id": "_1_while_0_e_o9", "label": "Next, nonclocked"}},
                {"data": {"source": "_1_while_0_e_o9", "target": "_1_while_o8"}},
                {"data": {"id": "_1_while_o8", "label": "if (((0 + 1) < n))"}},
                {"data": {"source": "_1_while_o8", "target": "_1_edge_o5"}},
                {"data": {"source": "_1_while_o8", "target": "_1_f_o7"}},
                {"data": {"id": "_1_edge_o5", "label": "True, clocked"}},
                {"data": {"source": "_1_edge_o5", "target": "_1_while_1"}},
                {"data": {"id": "_1_while_1", "label": "i <= (i + 1)"}},
                {"data": {"source": "_1_while_1", "target": "_1_while_1_e"}},
                {"data": {"id": "_1_while_1_e", "label": "Next"}},
                {"data": {"source": "_1_while_1_e", "target": "_1_while_0"}},
                {"data": {"id": "_1_while_0", "label": "a <= (i + 1)"}},
                {"data": {"source": "_1_while_0", "target": "_1_while_0_e"}},
                {"data": {"id": "_1_while_0_e", "label": "Next"}},
                {"data": {"source": "_1_while_0_e", "target": "_1_while"}},
                {"data": {"id": "_1_while", "label": "if ((i < n))"}},
                {"data": {"source": "_1_while", "target": "_1_edge"}},
                {"data": {"source": "_1_while", "target": "_1_f"}},
                {"data": {"id": "_1_edge", "label": "True"}},
                {"data": {"source": "_1_edge", "target": "_1_while_1"}},
                {"data": {"id": "_1_f", "label": "False"}},
                {"data": {"source": "_1_f", "target": "_0"}},
                {"data": {"id": "_0", "label": "yield [i]"}},
                {"data": {"source": "_0", "target": "_0_e"}},
                {"data": {"id": "_0_e", "label": "Next"}},
                {"data": {"source": "_0_e", "target": "_statelmaodone"}},
                {"data": {"id": "_statelmaodone", "label": "done"}},
                {"data": {"id": "_1_f_o7", "label": "False, nonclocked"}},
                {"data": {"source": "_1_f_o7", "target": "_0_o6"}},
                {"data": {"id": "_0_o6", "label": "yield [(0 + 1)]"}},
                {"data": {"source": "_0_o6", "target": "_0_e"}},
                {"data": {"id": "_1_f_o12", "label": "False, clocked"}},
                {"data": {"source": "_1_f_o12", "target": "_0"}},
            ],
        )
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
