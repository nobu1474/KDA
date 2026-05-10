import plotly.graph_objects as go


def plot_3d_point_cloud(points, title="Sphere", equal_aspect=False):
    """Plot a 3D point cloud."""
    import numpy as np
    if isinstance(points, list):
        points = np.vstack(points)
    
    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=points[:, 0],
                y=points[:, 1],
                z=points[:, 2],
                mode="markers",
                marker=dict(
                    size=3,
                    color=points[:, 2],
                    colorscale="Viridis",
                    opacity=0.8,
                ),
            )
        ]
    )

    aspectmode = "data" if equal_aspect else "cube"

    fig.update_layout(
        title=f"3D Point Cloud on Unit {title}",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode=aspectmode,
        ),
    )
    fig.show()


__all__ = ["plot_3d_point_cloud"]
