import plotly.graph_objects as go
from plotly.subplots import make_subplots
import itertools
import numpy as np
from tqdm import tqdm

import plotly.colors as pcolors
from core.open_curve_jones import open_curve_jones_polynomial, open_curve_PJP
from functions import format_jones_polynomial

def _evaluate_jones(poly, t_val):
    value = 0.0

    for exp, coeff in poly.items():
        if isinstance(exp, tuple):
            exp_val = float(exp[0]) / float(exp[1])
        else:
            exp_val = float(exp)

        value += coeff * (t_val ** exp_val)

    return float(value)

def _merge_connected_segments(segments):
    merged = []
    i = 0

    while i < len(segments):
        current = segments[i]

        while i + 1 < len(segments) and np.allclose(
            current[-1], segments[i + 1][0]
        ):
            # 重複する接続点を除いて結合
            current = np.vstack([current, segments[i + 1][1:]])
            i += 1

        merged.append(current)
        i += 1

    return merged

def facet_to_curves(facet, polylines):
    polys = []
    simplex = facet["simplex"]
    for p_idx in simplex: # simplexはファセットの頂点のインデックスのリストで、ポリラインのインデックスに対応させる
        if p_idx < len(polylines):
            poly = np.array(polylines[p_idx])
            polys.append(poly)
    polys = _merge_connected_segments(polys)  # 必要に応じて接続されたセグメントを結合
    return polys


def plot_birth_death_pairs_by_dimension(
    birth_death_pairs,
    title_prefix="Birth-Death Diagram",
    show_diagonal=True,
    plot_type="barcode",
    single_figure=True,
    points=None,
    polylines=None,
    run_server=True,
    host="127.0.0.1",
    port=8050,
    app_debug=False,
    t_val=10.0
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

        weights = []
        jones_polys = []
        w = 1.0
        for p in tqdm(pairs, desc=f"Jones polynomial {dim}"):
            polys = facet_to_curves(p, polylines) if polylines is not None else None
            
            # jp = open_curve_jones_polynomial(polys) if polys else {0: 1.0}
            jp = open_curve_PJP(polys) if polys else {0: 1.0}
            w = _evaluate_jones(jp, t_val) 
            
            weights.append(w)
            jones_polys.append(jp)

        min_w = min(weights)
        max_w = max(weights)

        range_w = max(max_w - min_w, 1e-12)

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
            sorted_pairs_and_weights = sorted(
                zip(pairs, weights, jones_polys),
                key=lambda pw: (float(pw[0]["birth"]), float(pw[0]["death"]) if pw[0]["death"] is not None else float("inf"))
            )
            
            for i, (p, w, jp) in enumerate(sorted_pairs_and_weights):
                b = float(p["birth"])
                if p["death"] is None:
                    d = infinite_y
                    is_infinite = True
                else:
                    d = float(p["death"])
                    is_infinite = False
                    
                # Jones重みによる色付け
                if points is not None:

                    norm_w = (w - min_w) / range_w

                    color = pcolors.sample_colorscale(
                        "Viridis",
                        [norm_w]
                    )[0]

                    hover_text = (
                        f"birth={b:.6f}<br>"
                        f"death={'∞' if is_infinite else f'{d:.6f}'}<br>"
                        # f"Jones polynomial={format_jones_polynomial(jp)}<br>" # 一旦非表示
                        f"Jones(t={t_val})={w:.6f}<br>"
                        f"simplex={p['simplex']}"
                        "<extra></extra>"
                    )
                else:

                    color = "#d62728" if is_infinite else "#1f77b4"

                    hover_text = (
                        f"birth={b:.6f}<br>"
                        f"death={'∞' if is_infinite else f'{d:.6f}'}"
                        "<extra></extra>"
                    )

                add_trace(
                    go.Scatter(
                        x=[b, d],
                        y=[i, i],
                        customdata=[p["simplex"], p["simplex"]],
                        mode="lines",
                        line=dict(
                            color=color,
                            width=4,
                        ),
                        showlegend=False,
                        hovertemplate=hover_text,
                    )
                )
            
            add_vline(
                x=infinite_y,
                line=dict(color="#d62728", dash="dot", width=1),
                annotation_text="∞",
                annotation_position="top left",
            )

            # カラーバー
            if max_w > min_w:
                add_trace(
                    go.Scatter(
                        x=[None],
                        y=[None],
                        mode="markers",
                        marker=dict(
                            colorscale="Viridis",
                            cmin=min_w,
                            cmax=max_w,
                            showscale=True,
                            colorbar=dict(
                                title=f"Jones(t={t_val})"
                            ),
                        ),
                        showlegend=False,
                        hoverinfo="skip",
                    )
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
        
        if isinstance(points, list) and len(points) > 0 and isinstance(points[0], np.ndarray):
            pts_arr = np.vstack(points)
            base_xs, base_ys, base_zs = [], [], []
            for comp in points:
                base_xs.extend(comp[:, 0].tolist() + [None])
                base_ys.extend(comp[:, 1].tolist() + [None])
                base_zs.extend(comp[:, 2].tolist() + [None])
        else:
            pts_arr = np.array(points)
            base_xs, base_ys, base_zs = pts_arr[:, 0], pts_arr[:, 1], pts_arr[:, 2]

        base_trace = go.Scatter3d(
            x=base_xs, y=base_ys, z=base_zs,
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
            hx, hy, hz = [], [], []

            if polylines is not None:
                # Polylines mode: highlight entire sequences of points
                for p_idx in simplex:
                    if p_idx < len(polylines):
                        poly = np.array(polylines[p_idx])
                        # Add lines for this polyline
                        for i in range(len(poly) - 1):
                            highlight_xs.extend([poly[i, 0], poly[i+1, 0], None])
                            highlight_ys.extend([poly[i, 1], poly[i+1, 1], None])
                            highlight_zs.extend([poly[i, 2], poly[i+1, 2], None])
                        hx.extend(poly[:, 0].tolist())
                        hy.extend(poly[:, 1].tolist())
                        hz.extend(poly[:, 2].tolist())
            else:
                # Default points mode: highlight individual points and connect them
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
