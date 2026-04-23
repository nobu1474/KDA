import numpy as np
import plotly.graph_objects as go

from core.crossings import project_to_2D
from core.jones import format_jones_polynomial


def _canonical_poly_key(poly):
    """Convert polynomial dict into a stable comparable key."""
    return tuple(sorted(poly.items(), key=lambda item: str(item[0])))


def plot_poly_map_on_sphere(poly_map, title="Jones polynomial classes on sphere"):
    """Plot projection directions on a sphere, colored by Jones polynomial class."""
    if not poly_map:
        raise ValueError("poly_map is empty")

    n_projection_directions = len(poly_map)

    grouped_points = {}
    for projection_vector, polynomial in poly_map.items():
        key = _canonical_poly_key(polynomial)
        if key not in grouped_points:
            grouped_points[key] = {
                "points": [],
                "label": format_jones_polynomial(polynomial),
            }
        grouped_points[key]["points"].append(np.asarray(projection_vector, dtype=float))

    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]

    fig = go.Figure()
    for index, (_poly_key, info) in enumerate(grouped_points.items()):
        points = np.array(info["points"])
        fig.add_trace(
            go.Scatter3d(
                x=points[:, 0],
                y=points[:, 1],
                z=points[:, 2],
                mode="markers",
                marker=dict(size=5, color=colors[index % len(colors)], opacity=0.9),
                name=info["label"],
                hovertemplate=(
                    "x=%{x:.3f}<br>y=%{y:.3f}<br>z=%{z:.3f}<br>"
                    + "<extra>"
                    + info["label"]
                    + "</extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"Distribution of Jones polynomials ({n_projection_directions} projection directions)",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="cube",
        ),
        legend_title="Jones polynomial",
    )

    fig.show()
    return fig


def plot_distinct_jones_poly_diagrams(
    curves,
    poly_map,
    title="Jones polynomial diagrams by projection direction",
):
    """Plot one 2D diagram per distinct Jones polynomial class."""
    if not poly_map:
        raise ValueError("poly_map is empty")

    if not curves or len(curves) == 0:
        raise ValueError("curves list is empty")

    poly_to_direction = {}
    for direction_tuple, polynomial in poly_map.items():
        poly_key = _canonical_poly_key(polynomial)
        if poly_key not in poly_to_direction:
            direction_vector = np.asarray(direction_tuple, dtype=float)
            direction_vector = direction_vector / np.linalg.norm(direction_vector)
            poly_to_direction[poly_key] = {
                "direction": direction_vector,
                "polynomial": polynomial,
                "label": format_jones_polynomial(polynomial),
            }

    for poly_idx, (_poly_key, info) in enumerate(poly_to_direction.items(), start=1):
        direction = info["direction"]
        jp_label = info["label"]

        diagram_2d = project_to_2D(curves[0], direction)

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=diagram_2d[:, 0],
                    y=diagram_2d[:, 1],
                    mode="markers",
                    marker=dict(size=6, color="blue", opacity=0.85),
                )
            ]
        )

        fig.update_layout(
            title=(
                f"{title} {poly_idx}: {jp_label}<br>"
                f"Projection direction: ({direction[0]:.3f}, {direction[1]:.3f}, {direction[2]:.3f})"
            ),
            xaxis_title="X",
            yaxis_title="Y",
            yaxis_scaleanchor="x",
            yaxis_scaleratio=1,
            showlegend=False,
        )

        fig.show()

    print(f"\nDisplayed {len(poly_to_direction)} distinct Jones polynomials")


__all__ = [
    "plot_poly_map_on_sphere",
    "plot_distinct_jones_poly_diagrams",
]
