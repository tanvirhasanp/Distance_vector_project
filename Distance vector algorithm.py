import networkx as nx
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import math

# Initialize the Dash app
app = Dash(__name__)
traffic_graph = nx.DiGraph()
layouts = ["spring", "circular", "force-directed layout", "random", "shell"]

# Layout
app.layout = html.Div(
    style={"fontFamily": "Arial", "padding": "20px", "backgroundColor": "#1e272e", "color": "#f5f6fa"},
    children=[
        html.H1("Distance Vector Algorithm and Shortest Path Finder", style={"textAlign": "center"}),

        # Input: Nodes and Edges
        html.Div(
            style={"marginBottom": "20px", "padding": "10px", "backgroundColor": "#2f3640", "borderRadius": "10px"},
            children=[
                html.Label("Enter nodes (comma-separated):", style={"color": "#00a8ff"}),
                dcc.Input(id="nodes_input", type="text", placeholder="e.g., A,B,C,D", style={"width": "100%"}),
                html.Label("Enter edges (format: 'u,v,cost' separated by newlines):", style={"color": "#00a8ff", "marginTop": "10px"}),
                dcc.Textarea(
                    id="edges_input",
                    placeholder="e.g., A,B,10\nB,C,5\nC,D,15",
                    style={"width": "100%", "height": "100px"}
                ),
                html.Button(
                    "Generate Graph", id="generate_graph", n_clicks=0,
                    style={"marginTop": "10px", "backgroundColor": "#6c5ce7", "color": "white", "borderRadius": "5px"}
                ),
                html.Label("Choose Graph Layout:", style={"color": "#00a8ff", "marginTop": "10px"}),
                dcc.Dropdown(
                    id="layout_dropdown",
                    options=[{"label": layout.title(), "value": layout} for layout in layouts],
                    value="spring",
                    style={"marginTop": "10px", "color": "#000"}
                ),
                html.Button(
                    "Regenerate Layout", id="regenerate_layout", n_clicks=0,
                    style={"marginTop": "10px", "backgroundColor": "#4cd137", "color": "white", "borderRadius": "5px"}
                ),
            ]
        ),

        # Shortest Path Inputs
        html.Div(
            style={"marginBottom": "20px", "padding": "10px", "backgroundColor": "#2f3640", "borderRadius": "10px"},
            children=[
                html.Label("Find Shortest Path:", style={"color": "#00a8ff"}),
                html.Br(),
                dcc.Input(id="start_node", type="text", placeholder="Start node (e.g., A)", style={"width": "48%"}),
                html.Br(),
                html.Br(),
                dcc.Input(id="end_node", type="text", placeholder="End node (e.g., D)", style={"width": "48%"}),
                html.Br(),
                html.Button(
                    "Find Path", id="find_path", n_clicks=0,
                    style={"marginTop": "10px", "backgroundColor": "#4cd137", "color": "white", "borderRadius": "5px"}
                ),
                html.Div(id="path_result", style={"color": "#00a8ff", "marginTop": "10px"}),
            ]
        ),

        # Graph Visualization
        dcc.Graph(
            id="traffic_graph",
            style={"boxShadow": "0px 6px 12px rgba(0, 0, 0, 0.3)", "borderRadius": "10px"}
        ),

        # Distance Table
        html.Div(
            style={"marginTop": "20px", "padding": "10px", "backgroundColor": "#2f3640", "borderRadius": "10px"},
            children=[
                html.H3("Shortest Path Table:", style={"color": "#00a8ff"}),
                dash_table.DataTable(
                    id="distance_table",
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "textAlign": "center", "padding": "10px", "fontSize": "14px",
                        "border": "1px solid #ddd", "backgroundColor": "#2f3640", "color": "#f5f6fa"
                    },
                    style_header={"backgroundColor": "#00a8ff", "color": "white", "fontWeight": "bold"},
                )
            ]
        ),
    ]
)

# Callbacks
@app.callback(
    [Output("traffic_graph", "figure"),
     Output("path_result", "children"),
     Output("distance_table", "data"),
     Output("distance_table", "columns")],
    [Input("generate_graph", "n_clicks"),
     Input("find_path", "n_clicks"),
     Input("regenerate_layout", "n_clicks")],
    [State("nodes_input", "value"),
     State("edges_input", "value"),
     State("start_node", "value"),
     State("end_node", "value"),
     State("layout_dropdown", "value")]
)
def update_graph(n_generate, n_find, n_regenerate, nodes_input, edges_input, start_node, end_node, layout):
    global traffic_graph

    path_result = ""
    shortest_path_edges = []
    self_loop_node = None
    table_data = []
    table_columns = []

    # Generate Graph
    if n_generate and nodes_input and edges_input:
        traffic_graph.clear()
        nodes = nodes_input.split(",")
        traffic_graph.add_nodes_from(nodes)

        for edge in edges_input.strip().split("\n"):
            try:
                u, v, weight = edge.split(",")
                traffic_graph.add_edge(u.strip(), v.strip(), weight=float(weight.strip()))
            except ValueError:
                continue

    # Compute Shortest Path Table
    distances = {node: {n: float('inf') for n in traffic_graph.nodes} for node in traffic_graph.nodes}
    for node in traffic_graph.nodes:
        distances[node][node] = 0
    for u, v, data in traffic_graph.edges(data=True):
        distances[u][v] = data["weight"]

    for intermediate in traffic_graph.nodes:
        for u in traffic_graph.nodes:
            for v in traffic_graph.nodes:
                if distances[u][v] > distances[u][intermediate] + distances[intermediate][v]:
                    distances[u][v] = distances[u][intermediate] + distances[intermediate][v]

    table_columns = [{"name": node, "id": node} for node in traffic_graph.nodes]
    table_data = [
        {node: distances[src][node] if distances[src][node] != float('inf') else "INF" for node in traffic_graph.nodes}
        for src in traffic_graph.nodes
    ]

    # Find Shortest Path
    if n_find and start_node and end_node:
        if start_node.strip() == end_node.strip():
            path_result = f"Shortest Path: {start_node.strip()} -> {end_node.strip()}, Cost: 0"
            self_loop_node = start_node.strip()
        else:
            try:
                path = nx.shortest_path(traffic_graph, source=start_node.strip(), target=end_node.strip(), weight="weight")
                cost = nx.shortest_path_length(traffic_graph, source=start_node.strip(), target=end_node.strip(), weight="weight")
                path_result = f"Shortest Path: {' -> '.join(path)}, Cost: {cost}"
                shortest_path_edges = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
            except nx.NetworkXNoPath:
                path_result = "No path found."

    # Get Graph Layout
    if layout == "spring":
        pos = nx.spring_layout(traffic_graph)
    elif layout == "circular":
        pos = nx.circular_layout(traffic_graph)
    elif layout == "force-directed layout":
        pos = nx.kamada_kawai_layout(traffic_graph)
    elif layout == "random":
        pos = nx.random_layout(traffic_graph)
    elif layout == "shell":
        pos = nx.shell_layout(traffic_graph)

    # Visualize Graph
    edge_trace = go.Scatter(
        x=[], y=[], line=dict(width=2, color="#4cd137"), mode="lines"
    )
    shortest_path_trace = go.Scatter(
        x=[], y=[], line=dict(width=4, color="red"), mode="lines"
    )
    text_trace = go.Scatter(
        x=[], y=[], text=[], mode="text", textfont=dict(size=12, color="#00a8ff")
    )
    node_trace = go.Scatter(
        x=[], y=[], text=[], mode="markers+text", hoverinfo="text",
        marker=dict(size=20, color="#00a8ff", line=dict(width=2)),
        textfont=dict(size=14, color="white")
    )

    # Draw Edges and Weights
    for u, v, data in traffic_graph.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        weight = data["weight"]
        if (u, v) in shortest_path_edges:
            shortest_path_trace["x"] += (x0, x1, None)
            shortest_path_trace["y"] += (y0, y1, None)
        else:
            edge_trace["x"] += (x0, x1, None)
            edge_trace["y"] += (y0, y1, None)
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2 - 0.02
        text_trace["x"] += (mid_x,)
        text_trace["y"] += (mid_y,)
        text_trace["text"] += (f"{u},{v},{weight}",)

    # Draw Nodes and Handle Self-Loop
    for node in traffic_graph.nodes:
        x, y = pos[node]
        node_trace["x"] += (x,)
        node_trace["y"] += (y,)
        node_trace["text"] += (node,)
        if node == self_loop_node:
            # Add a self-loop (circle) for the node
            angle_step = math.pi / 4
            loop_x = [x + 0.05 * math.cos(angle_step * i) for i in range(9)]
            loop_y = [y + 0.05 * math.sin(angle_step * i) for i in range(9)]
            shortest_path_trace["x"] += loop_x + [None]
            shortest_path_trace["y"] += loop_y + [None]
            node_trace["marker"]["color"] = ["red" if n == self_loop_node else "#00a8ff" for n in traffic_graph.nodes]

    fig = go.Figure(data=[edge_trace, shortest_path_trace, text_trace, node_trace])
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="#1e272e")

    return fig, path_result, table_data, table_columns


if __name__ == "__main__":
    app.run_server(debug=True)
