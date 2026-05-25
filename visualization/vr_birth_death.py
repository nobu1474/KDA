import plotly.graph_objects as go
from plotly.subplots import make_subplots
import itertools
import numpy as np


def plot_birth_death_pairs_by_dimension(
    birth_death_pairs,
    title_prefix="Birth-Death Diagram",
    show_diagonal=True,
    plot_type="barcode",
    single_figure=True,
    points=None,
    run_server=True,
    host="127.0.0.1",
    port=8050,
    app_debug=False,
):
    """Visualize birth-death pairs for each dimension."""
    if not birth_death_pairs:
        raise ValueError("birth_death_pairs is empty")

    if isinstance(birth_death_pairs, dict):
        pairs_by_dim = {int(dim): list(pairs) for dim, pairs in birth_death_pairs.items()}
    else:
        pairs_by_dim = {}
        for pair in birth_death_pairs:
            dim = int(pair["dimension"])
            normalized_pair = {
                "simplex": pair["simplex"],
                "birth": pair["birth"],
                "death": pair["death"],
                "lifetime": pair["lifetime"],
            }
            pairs_by_dim.setdefault(dim, []).append(normalized_pair)

    figures_by_dimension = {}

    if not pairs_by_dim:
        return figures_by_dimension

    max_dim = max(pairs_by_dim.keys())
    dims_to_plot = [dim for dim in sorted(pairs_by_dim.keys()) if dim != max_dim]

    if not dims_to_plot:
        return figures_by_dimension

    if single_figure:
        fig_main = make_subplots(
            rows=1, cols=len(dims_to_plot),
            subplot_titles=[f"Dimension {dim}" for dim in dims_to_plot],
            horizontal_spacing=0.05
        )

    global_max_axis = 1.0
    global_max_features = 0
    for dim in dims_to_plot:
        pairs = pairs_by_dim[dim]
        finite_deaths = [float(p["death"]) for p in pairs if p["death"] is not None]
        all_births = [float(p["birth"]) for p in pairs]
        curr_max = max(all_births) if all_births else 0.0
        if finite_deaths:
            curr_max = max(curr_max, max(finite_deaths))
        global_max_axis = max(global_max_axis, curr_max)
        global_max_features = max(global_max_features, len(pairs))

    infinite_y = global_max_axis * 1.05
    pad = global_max_axis * 0.08

    for col_idx, dim in enumerate(dims_to_plot, start=1):
        pairs = pairs_by_dim[dim]
        finite_pairs = [p for p in pairs if p["death"] is not None]
        infinite_pairs = [p for p in pairs if p["death"] is None]

        finite_births = [float(p["birth"]) for p in finite_pairs]
        finite_deaths = [float(p["death"]) for p in finite_pairs]

        if not single_figure:
            fig = go.Figure()

        def add_trace(trace, **kwargs):
            if single_figure:
                fig_main.add_trace(trace, row=1, col=col_idx, **kwargs)
            else:
                fig.add_trace(trace, **kwargs)

        def add_hline(y, **kwargs):
            if single_figure:
                fig_main.add_hline(y=y, row=1, col=col_idx, **kwargs)
            else:
                fig.add_hline(y=y, **kwargs)

        def add_vline(x, **kwargs):
            if single_figure:
                fig_main.add_vline(x=x, row=1, col=col_idx, **kwargs)
            else:
                fig.add_vline(x=x, **kwargs)

        if plot_type == "barcode":
            # Barcode plot logic similar to plot_PJP
            # Sort pairs by birth time, then death time
            sorted_pairs = sorted(
                pairs,
                key=lambda p: (float(p["birth"]), float(p["death"]) if p["death"] is not None else float("inf"))
            )
            
            x_finite_lines, y_finite_lines = [], []
            x_infinite_lines, y_infinite_lines = [], []
            customdata_finite = []
            customdata_infinite = []
            
            for i, p in enumerate(sorted_pairs):
                b = float(p["birth"])
                if p["death"] is None:
                    x_infinite_lines.extend([b, infinite_y, None])
                    y_infinite_lines.extend([i, i, None])
                    customdata_infinite.extend([p["simplex"], p["simplex"], p["simplex"]])
                else:
                    d = float(p["death"])
                    x_finite_lines.extend([b, d, None])
                    y_finite_lines.extend([i, i, None])
                    customdata_finite.extend([p["simplex"], p["simplex"], p["simplex"]])
                    
            if x_finite_lines:
                add_trace(
                    go.Scatter(
                        x=x_finite_lines,
                        y=y_finite_lines,
                        customdata=customdata_finite,
                        mode="lines",
                        line=dict(color="#1f77b4", width=3),
                        name="finite",
                        hovertemplate="Feature %{customdata}<extra></extra>" if points is not None else None,
                        hoverinfo="skip" if points is None else None,
                    )
                )
            if x_infinite_lines:
                add_trace(
                    go.Scatter(
                        x=x_infinite_lines,
                        y=y_infinite_lines,
                        customdata=customdata_infinite,
                        mode="lines",
                        line=dict(color="#d62728", width=3),
                        name="infinite",
                        hovertemplate="Feature %{customdata}<extra></extra>" if points is not None else None,
                        hoverinfo="skip" if points is None else None,
                    )
                )
                add_vline(
                    x=infinite_y,
                    line=dict(color="#d62728", dash="dot", width=1),
                    annotation_text="∞",
                    annotation_position="top left",
                )
                
            if not single_figure:
                fig.update_layout(
                    title=f"{title_prefix} - Barcode (dimension={dim})",
                    xaxis_title="Filtration value",
                    yaxis_title="Features",
                    yaxis=dict(showticklabels=False, range=[-1, global_max_features]),
                    xaxis=dict(range=[0.0, infinite_y + pad]),
                    width=600, height=600
                )
            else:
                fig_main.update_xaxes(title_text="Filtration value", range=[0.0, infinite_y + pad], row=1, col=col_idx)
                fig_main.update_yaxes(title_text="Features", showticklabels=False, range=[-1, global_max_features], row=1, col=col_idx)
        else:
            if finite_pairs:
                add_trace(
                    go.Scatter(
                        x=finite_births,
                        y=finite_deaths,
                        customdata=[p["simplex"] for p in finite_pairs],
                        mode="markers",
                        marker=dict(size=7, color="#1f77b4", opacity=0.9),
                        name="finite",
                        hovertemplate="birth=%{x:.6f}<br>death=%{y:.6f}<br>Feature %{customdata}<extra>finite</extra>" if points is not None else "birth=%{x:.6f}<br>death=%{y:.6f}<extra>finite</extra>",
                    )
                )

            if infinite_pairs:
                inf_births = [float(p["birth"]) for p in infinite_pairs]
                inf_deaths = [infinite_y] * len(inf_births)
                add_trace(
                    go.Scatter(
                        x=inf_births,
                        y=inf_deaths,
                        customdata=[p["simplex"] for p in infinite_pairs],
                        mode="markers",
                        marker=dict(size=8, symbol="x", color="#d62728", opacity=0.95),
                        name="death=None (infinite)",
                        hovertemplate="birth=%{x:.6f}<br>death=∞<br>Feature %{customdata}<extra>infinite</extra>" if points is not None else "birth=%{x:.6f}<br>death=∞<extra>infinite</extra>",
                    )
                )

                add_hline(
                    y=infinite_y,
                    line=dict(color="#d62728", dash="dot", width=1),
                    annotation_text="death=∞ (表示用)",
                    annotation_position="top left",
                )

            if show_diagonal:
                diag_max = max(global_max_axis, infinite_y)
                add_trace(
                    go.Scatter(
                        x=[0.0, diag_max],
                        y=[0.0, diag_max],
                        mode="lines",
                        line=dict(color="#7f7f7f", dash="dash"),
                        name="y=x",
                        hoverinfo="skip",
                    )
                )

            if not single_figure:
                fig.update_layout(
                    title=f"{title_prefix} (dimension={dim})",
                    xaxis_title="Birth",
                    yaxis_title="Death",
                    xaxis=dict(range=[0.0, max(global_max_axis, infinite_y) + pad]),
                    yaxis=dict(range=[0.0, max(global_max_axis, infinite_y) + pad]),
                    yaxis_scaleanchor="x",
                    yaxis_scaleratio=1,
                    width=600, height=600
                )
            else:
                fig_main.update_xaxes(title_text="Birth", range=[0.0, max(global_max_axis, infinite_y) + pad], row=1, col=col_idx)
                fig_main.update_yaxes(title_text="Death", range=[0.0, max(global_max_axis, infinite_y) + pad], scaleanchor=f"x{col_idx if col_idx > 1 else ''}", scaleratio=1, row=1, col=col_idx)

        if not single_figure:
            figures_by_dimension[dim] = fig

    if single_figure:
        fig_main.update_layout(
            title=title_prefix, 
            showlegend=False,
            template="plotly_white",
            width=600 * len(dims_to_plot),
            height=600,
            margin=dict(b=80)
        )
        figures_by_dimension["main"] = fig_main

    if points is not None and run_server:
        try:
            import dash
            from dash import html, dcc
            from dash.dependencies import Input, Output
        except ImportError:
            print("Dash is required for interactivity. Please pip install dash.")
            return figures_by_dimension
            
        app = dash.Dash(__name__)
        pts_arr = np.array(points)
        base_trace = go.Scatter3d(
            x=pts_arr[:, 0], y=pts_arr[:, 1], z=pts_arr[:, 2],
            mode="markers+lines", marker=dict(size=4, color="lightgrey", opacity=0.5),
            line=dict(color="lightgrey", width=2),
            name="Point Cloud", hoverinfo="skip"
        )
        base_layout = go.Layout(
            title="Highlighted Facet", margin=dict(l=0, r=0, b=0, t=40),
            scene=dict(aspectmode="data")
        )
        base_3d_fig = go.Figure(data=[base_trace], layout=base_layout)
        
        barcode_graphs = []
        if single_figure:
            barcode_graphs.append(dcc.Graph(id='barcode-graph-main', figure=fig_main, style={'height': '100%'}))
        else:
            for dim in dims_to_plot:
                barcode_graphs.append(dcc.Graph(id=f'barcode-graph-{dim}', figure=figures_by_dimension[dim]))

        app.layout = html.Div(style={'display': 'flex', 'flexDirection': 'row', 'height': '95vh'}, children=[
            html.Div(style={'width': '50%', 'padding': '10px', 'overflowY': 'auto'}, children=barcode_graphs),
            html.Div(dcc.Graph(id='scatter-3d', figure=base_3d_fig, style={'height': '100%'}), style={'width': '50%', 'padding': '10px'})
        ])
        
        inputs = [Input('barcode-graph-main', 'hoverData')] if single_figure else [Input(f'barcode-graph-{dim}', 'hoverData') for dim in dims_to_plot]
        
        @app.callback(Output('scatter-3d', 'figure'), *inputs)
        def update_3d_scatter(*hover_datas):
            from dash import ctx
            if not ctx.triggered:
                return base_3d_fig
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            hoverData = None
            if single_figure:
                hoverData = hover_datas[0]
            else:
                for idx, dim in enumerate(dims_to_plot):
                    if trigger_id == f'barcode-graph-{dim}':
                        hoverData = hover_datas[idx]
                        break
                        
            if not hoverData:
                return base_3d_fig
                
            simplex = hoverData['points'][0].get('customdata')
            if not simplex:
                return base_3d_fig
                
            highlight_xs, highlight_ys, highlight_zs = [], [], []
            for u, v in itertools.combinations(simplex, 2):
                highlight_xs.extend([pts_arr[u, 0], pts_arr[v, 0], None])
                highlight_ys.extend([pts_arr[u, 1], pts_arr[v, 1], None])
                highlight_zs.extend([pts_arr[u, 2], pts_arr[v, 2], None])
            
            hx = pts_arr[simplex, 0]
            hy = pts_arr[simplex, 1]
            hz = pts_arr[simplex, 2]
            
            hl_lines = go.Scatter3d(
                x=highlight_xs, y=highlight_ys, z=highlight_zs,
                mode="lines", line=dict(color="red", width=5), hoverinfo="skip"
            )
            hl_markers = go.Scatter3d(
                x=hx, y=hy, z=hz,
                mode="markers", marker=dict(color="red", size=8), hoverinfo="skip"
            )
            return go.Figure(data=[base_trace, hl_lines, hl_markers], layout=base_layout)
            
        app.run(debug=app_debug, host=host, port=port)
    else:
        if not single_figure:
            for dim, fig in figures_by_dimension.items():
                if dim != "main":
                    fig.show()
        if single_figure:
            fig_main.show()

    return figures_by_dimension


__all__ = ["plot_birth_death_pairs_by_dimension"]
