import plotly.graph_objects as go


def plot_birth_death_pairs_by_dimension(
    birth_death_pairs,
    title_prefix="Birth-Death Diagram",
    show_diagonal=True,
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

    for dim in sorted(pairs_by_dim.keys()):
        pairs = pairs_by_dim[dim]
        finite_pairs = [p for p in pairs if p["death"] is not None]
        infinite_pairs = [p for p in pairs if p["death"] is None]

        finite_births = [float(p["birth"]) for p in finite_pairs]
        finite_deaths = [float(p["death"]) for p in finite_pairs]

        all_births = [float(p["birth"]) for p in pairs]
        max_axis = max(all_births) if all_births else 1.0
        if finite_deaths:
            max_axis = max(max_axis, max(finite_deaths))
        if max_axis <= 0:
            max_axis = 1.0

        infinite_y = max_axis * 1.05
        pad = max_axis * 0.08

        fig = go.Figure()

        if finite_pairs:
            fig.add_trace(
                go.Scatter(
                    x=finite_births,
                    y=finite_deaths,
                    mode="markers",
                    marker=dict(size=7, color="#1f77b4", opacity=0.9),
                    name="finite",
                    hovertemplate="birth=%{x:.6f}<br>death=%{y:.6f}<extra>finite</extra>",
                )
            )

        if infinite_pairs:
            inf_births = [float(p["birth"]) for p in infinite_pairs]
            inf_deaths = [infinite_y] * len(inf_births)
            fig.add_trace(
                go.Scatter(
                    x=inf_births,
                    y=inf_deaths,
                    mode="markers",
                    marker=dict(size=8, symbol="x", color="#d62728", opacity=0.95),
                    name="death=None (infinite)",
                    hovertemplate="birth=%{x:.6f}<br>death=∞<extra>infinite</extra>",
                )
            )

            fig.add_hline(
                y=infinite_y,
                line=dict(color="#d62728", dash="dot", width=1),
                annotation_text="death=∞ (表示用)",
                annotation_position="top left",
            )

        if show_diagonal:
            diag_max = max(max_axis, infinite_y)
            fig.add_trace(
                go.Scatter(
                    x=[0.0, diag_max],
                    y=[0.0, diag_max],
                    mode="lines",
                    line=dict(color="#7f7f7f", dash="dash"),
                    name="y=x",
                    hoverinfo="skip",
                )
            )

        fig.update_layout(
            title=f"{title_prefix} (dimension={dim})",
            xaxis_title="Birth",
            yaxis_title="Death",
            xaxis=dict(range=[0.0, max(max_axis, infinite_y) + pad]),
            yaxis=dict(range=[0.0, max(max_axis, infinite_y) + pad]),
            yaxis_scaleanchor="x",
            yaxis_scaleratio=1,
        )

        fig.show()
        figures_by_dimension[dim] = fig

    return figures_by_dimension


__all__ = ["plot_birth_death_pairs_by_dimension"]
