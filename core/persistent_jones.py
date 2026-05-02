import plotly.graph_objects as go
import plotly.colors as pcolors
import numpy as np
from model.knot import Knot


def _downsample_curve(curve, max_segments):
    if len(curve) <= max_segments + 1:
        return curve
    sample_count = max_segments + 1
    idx = np.linspace(0, len(curve) - 1, sample_count, dtype=int)
    return [curve[i] for i in idx]


def _get_shortcut_curve(curve, r, max_segments=12):
    n = len(curve)
    if n <= 3:
        return curve
    
    new_curve = [curve[0]]
    i = 0
    # ヒューリスティックなショートカットの構築：
    # パラメータ順に進む中で、距離が r 以下の最も遠いインデックスへジャンプする。
    # カーブ全体の位相を無視して潰しすぎないように、最大でも n // 2 までのジャンプに制限する。
    while i < n - 1:
        best_j = i + 1
        for j in range(min(n - 1, i + n // 2), i, -1):
            if np.linalg.norm(curve[i] - curve[j]) <= r:
                best_j = j
                break
        i = best_j
        new_curve.append(curve[i])
        
    return _downsample_curve(new_curve, max_segments=max_segments)

def plot_persistent_jones_polynomial(curve, filtration, bd_pairs, max_radii=20, n_directions=1, max_segments=12):
    """
    Plot the Persistent Jones Polynomial (similar to Section 5.2).
    
    This function computes the Jones polynomial of the knot at various 
    filtration values (radii) and visualizes the evolution of the 
    polynomial coefficients over the filtration parameter.
    
    Args:
        curve: The sequence of points forming the knot.
        filtration: The Vietoris-Rips filtration.
        bd_pairs: Birth-death pairs of the facets.
        max_radii: Number of radii to sample.
        n_directions: Number of projection directions to average the Jones polynomial over.
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
    
    # n_directions の分の射影ベクトルを生成
    np.random.seed(42)  # 可視化の再現性のため
    directions = []
    for _ in range(n_directions):
        v = np.random.randn(3)
        norm = np.linalg.norm(v)
        if norm > 0:
            directions.append(v / norm)
            
    if len(directions) == 0:
        directions.append(np.array([0, 0, 1]))

    for r in radii:
        # 半径 r におけるショートカット曲線（簡約表現）を構築
        sc_curve = _get_shortcut_curve(curve, r, max_segments=max_segments)
        segments = [sc_curve[i:i + 2] for i in range(len(sc_curve) - 1)]
        
        # 複数方向での Jones Polynomial を計算して平均する
        avg_poly = {}
        for d in directions:
            jp = Knot(segments, projection_vector=d).jones_polynomial
            for exp, coeff in jp.items():
                avg_poly[exp] = avg_poly.get(exp, 0) + coeff / len(directions)
                
        # 小さすぎる係数の丸め
        avg_poly = {exp: coeff for exp, coeff in avg_poly.items() if abs(coeff) > 1e-5}
        if not avg_poly:
            avg_poly = {0: 1.0}  # trivially point-like (trivial knot)

        poly_history.append((r, avg_poly))

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


from plotly.subplots import make_subplots

def plot_PJP(
    birth_death_pairs,
    title_prefix="Persistence Barcode",
    max_dim=2,
    single_figure=True,
    points=None,
    t_val=10.0,
):
    """Visualize birth-death pairs as a barcode (horizontal lines) for each dimension."""
    if not birth_death_pairs:
        raise ValueError("birth_death_pairs is empty")

    if isinstance(birth_death_pairs, dict):
        pairs_by_dim = {int(dim): list(pairs) for dim, pairs in birth_death_pairs.items() if int(dim) <= max_dim}
    else:
        pairs_by_dim = {}
        for pair in birth_death_pairs:
            dim = int(pair["dimension"])
            if dim <= max_dim:
                normalized_pair = {
                    "simplex": pair["simplex"],
                    "birth": pair["birth"],
                    "death": pair["death"],
                    "lifetime": pair["lifetime"],
                }
                pairs_by_dim.setdefault(dim, []).append(normalized_pair)

    if not pairs_by_dim:
        return {}

    # 全次元共通の最大X, Y（特徴数）を計算
    global_max_x = 0.0
    global_max_features = 0

    for dim, pairs in pairs_by_dim.items():
        # 表示対象の次元(dim <= max_dim)のみを考慮する
        if dim > max_dim:
            continue
            
        all_births = [float(p["birth"]) for p in pairs]
        finite_deaths = [float(p["death"]) for p in pairs if p["death"] is not None]
        
        curr_max_x = max(all_births) if all_births else 0.0
        if finite_deaths:
            curr_max_x = max(curr_max_x, max(finite_deaths))
        global_max_x = max(global_max_x, curr_max_x)
        global_max_features = max(global_max_features, len(pairs))

    if global_max_x <= 0:
        global_max_x = 1.0

    infinite_death = global_max_x * 1.1
    dims_to_plot = sorted(pairs_by_dim.keys())

    if single_figure:
        fig = make_subplots(
            rows=1, cols=len(dims_to_plot),
            subplot_titles=[f"Dim {dim} (features={len(pairs_by_dim[dim])})" for dim in dims_to_plot],
            horizontal_spacing=0.05
        )

    figures_by_dimension = {}

    for col_idx, dim in enumerate(dims_to_plot, start=1):
        pairs = sorted(pairs_by_dim[dim], key=lambda p: float(p["birth"]))

        if not single_figure:
            fig = go.Figure()

        # 各FacetのJones多項式による重み(t_valを代入)を計算
        weights = []
        for p in pairs:
            w = 1.0
            if points is not None and len(p["simplex"]) >= 3:
                try:
                    sc_curve = [points[v] for v in p["simplex"]]
                    segs = [[sc_curve[k], sc_curve[(k+1) % len(sc_curve)]] for k in range(len(sc_curve))]
                    jp = Knot(segs, projection_vector=np.array([0, 0, 1])).jones_polynomial
                    print(f"Debug: simplex={p['simplex']}, jp={Knot(segs, projection_vector=np.array([0, 0, 1])).jones_polynomial_str}")
                    w = 0.0
                    for exp, coeff in jp.items():
                        if isinstance(exp, tuple):
                            p_val = float(exp[0]) / float(exp[1])
                        else:
                            p_val = float(exp)
                        w += coeff * (t_val ** p_val)
                except Exception as e:
                    print(f"Warning: knot calculation failed: {e}")
                    w = 1.0
            weights.append(w)
            
        min_w, max_w = (min(weights), max(weights)) if weights else (1.0, 1.0)
        diff_w = max_w - min_w
        print(f"Dimension {dim}: Jones polynomial (t={t_val}) Max - Min difference = {diff_w:.6f}")
        range_w = diff_w if diff_w > 0 else 1.0

        for i, (p, w) in enumerate(zip(pairs, weights)):
            b = float(p["birth"])
            d = float(p["death"]) if p["death"] is not None else infinite_death
            is_infinite = p["death"] is None
            
            if points is not None and len(p["simplex"]) >= 3:
                norm_w = (w - min_w) / range_w
                color = pcolors.sample_colorscale("Viridis", [norm_w])[0]
                hover_text = f"birth={b:.6f}<br>death={'∞' if is_infinite else f'{d:.6f}'}<br>weight(t={t_val})={w:.4f}<extra></extra>"
            else:
                color = "#d62728" if is_infinite else "#1f77b4"
                hover_text = f"birth={b:.6f}<br>death={'∞' if is_infinite else f'{d:.6f}'}<extra></extra>"

            scatter = go.Scatter(
                x=[b, d],
                y=[i, i],
                mode="lines",
                line=dict(color=color, width=5),
                name=f"Feature {i}",
                showlegend=False,
                hovertemplate=hover_text
            )
            
            if single_figure:
                fig.add_trace(scatter, row=1, col=col_idx)
            else:
                fig.add_trace(scatter)
                
        # ヒートマップの色凡例用ダミートレースを追加
        if points is not None and len(weights) > 0 and max_w > min_w:
            dummy_scatter = go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(
                    colorscale="Viridis",
                    cmin=min_w, cmax=max_w,
                    showscale=True,
                    colorbar=dict(
                        title=f"Dim {dim} Weight",
                        x=1.02 + 0.08 * (col_idx - 1),
                        len=0.8,
                        y=0.5
                    )
                ),
                showlegend=False,
                hoverinfo="none"
            )
            if single_figure:
                fig.add_trace(dummy_scatter, row=1, col=col_idx)
            else:
                fig.add_trace(dummy_scatter)

        if single_figure:
            # x軸の設定 (共通範囲)
            fig.update_xaxes(range=[0.0, infinite_death], row=1, col=col_idx, title_text="Filtration Value" if col_idx == 1 else "")
            
            # y軸の設定 (共通のFacet最大数に合わせる)
            fig.update_yaxes(
                range=[-1, global_max_features], # 0,1,2次元すべてで共通の高さにする
                showticklabels=False,
                row=1, col=col_idx,
                title_text="Feature Index" if col_idx == 1 else ""
            )

            # 破線の追加
            fig.add_vline(x=global_max_x, line=dict(color="#d62728", dash="dot", width=1), row=1, col=col_idx)
            
            # グラフの下に差分をテキストとして追加
            fig.add_annotation(
                text=f"Max-Min Diff: {diff_w:.4f}",
                x=0.5, y=-0.15,
                xref="x domain", yref="y domain",
                xanchor="center", yanchor="top",
                showarrow=False,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="black",
                row=1, col=col_idx
            )

        else:
            fig.add_vline(
                x=global_max_x,
                line=dict(color="#d62728", dash="dot", width=1),
                annotation_text="∞",
                annotation_position="top right"
            )
            
            # グラフの下に差分をテキストとして追加
            fig.add_annotation(
                text=f"Max-Min Diff: {diff_w:.4f}",
                xref="paper", yref="paper",
                x=0.5, y=-0.15,
                xanchor="center", yanchor="top",
                showarrow=False,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="black"
            )

            # 画面に入る一般的な高さに固定
            plot_size = 600
            fig.update_layout(
                title=f"{title_prefix} (dimension={dim}, features={len(pairs)})",
                xaxis_title="Filtration Value",
                yaxis_title="Feature Index",
                yaxis=dict(showticklabels=False, range=[-1, global_max_features]),
                xaxis=dict(range=[0.0, infinite_death]),
                template="plotly_white",
                width=plot_size,
                height=plot_size,
                margin=dict(b=80)
            )
            fig.show()
            figures_by_dimension[dim] = fig

    if single_figure:
        # 画面に入る一般的な高さに固定
        plot_size = 600
        fig.update_layout(
            title=title_prefix,
            template="plotly_white",
            width=plot_size * len(dims_to_plot),
            height=plot_size,
            margin=dict(b=80)
        )
        fig.show()
        return fig
    else:
        return figures_by_dimension
