import plotly.graph_objects as go
import numpy as np
from model.knot import Knot


def _downsample_curve(curve, max_segments):
    if len(curve) <= max_segments + 1:
        return curve
    sample_count = max_segments + 1
    idx = np.linspace(0, len(curve) - 1, sample_count, dtype=int)
    return [curve[i] for i in idx]


def plot_persistent_jones_polynomial(curve, filtration, bd_pairs, max_radii=40):
    """
    Plot the Persistent Jones Polynomial (similar to Section 5.2).
    
    This function computes the Jones polynomial of the knot at various 
    filtration values (radii) and visualizes the evolution of the 
    polynomial coefficients over the filtration parameter.
    
    Args:
        curve: The sequence of points forming the knot.
        filtration: The Vietoris-Rips filtration.
        bd_pairs: Birth-death pairs of the facets.
    """
    # Extract unique birth times (radii) from the birth-death pairs 
    # or filtration, we'll use a set of representative radii.
    
    # 実際には、論文の定義(3.2節)に従って、各filtration stepでの
    # knotの簡約表現（あるいはshortcutを考慮した多角形）を構築し、
    # Jones多項式を計算します。
    # ここでは骨組みとなる可視化の実装を提供します。
    
    radii = {0.0}

    if isinstance(bd_pairs, dict):
        for pairs in bd_pairs.values():
            for pair in pairs:
                if isinstance(pair, dict) and pair.get('birth') is not None:
                    radii.add(float(pair['birth']))

    if isinstance(filtration, list):
        for stage in filtration:
            if isinstance(stage, dict) and stage.get('radius') is not None:
                radii.add(float(stage['radius']))

    radii = sorted(radii)
    if len(radii) > int(max_radii):
        sample_idx = np.linspace(0, len(radii) - 1, int(max_radii), dtype=int)
        radii = [radii[i] for i in sample_idx]
    if not radii:
        radii = np.linspace(0, 1.0, 10).tolist()
        
    poly_history = []
    
    # Placeholder 実装では各 r で同じ curve を使うため、重い Jones 計算は1回だけ実行する。
    # 計算量が爆発しやすいので、可視化用途ではセグメント数を抑える。
    jones_curve = _downsample_curve(curve, max_segments=18)
    segments = [jones_curve[i:i + 2] for i in range(len(jones_curve) - 1)]
    base_jp = Knot(segments).jones_polynomial
    for r in radii:
        poly_history.append((r, base_jp))

    # Plotlyでヒートマップ(または散布図)を作成
    # x軸: radius, y軸: polynomial exponent, color: coefficient
    fig = go.Figure()
    
    x = []
    y = []
    text = []
    marker_colors = []
    marker_sizes = []
    
    for r, poly in poly_history:
        if isinstance(poly, dict):
            for exp, coeff in poly.items():
                if abs(coeff) > 1e-10:
                    x.append(r)
                    # Exponentを数値化(tupleならその和等)
                    y_val = exp if isinstance(exp, (int, float)) else sum(exp)
                    y.append(y_val)
                    marker_colors.append(coeff)
                    marker_sizes.append(abs(coeff) * 10 + 5)
                    text.append(f"r: {r:.3f}, exp: {exp}, coeff: {coeff}")
        elif isinstance(poly, str):
            # 文字列の場合はダミー
            pass
            
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode='markers',
        marker=dict(
            size=marker_sizes,
            color=marker_colors,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Coefficient')
        ),
        text=text,
        hoverinfo='text'
    ))

    fig.update_layout(
        title="Persistent Jones Polynomial",
        xaxis_title="Filtration value (Radius)",
        yaxis_title="Degree of t",
        template="plotly_white"
    )
    
    fig.show()
    return fig
