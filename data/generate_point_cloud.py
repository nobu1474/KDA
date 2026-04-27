from math import cos, sin

import numpy as np



def generate_unit_nm_torus_points(n_points, n=2, m=3,seed=None):
    """Generates N points uniformly sampled on a unit (n,m)-torus in 3D."""
    if seed is not None:
        np.random.seed(seed)

    # Generate random points in 3D space
    # 一つ目をr、二つ目をthetaとする
    points = np.random.rand(n_points, 2) # [0, 1)
    points[:, 0] *= 2
    points[:, 0] -= 1  # -1 <= r < 1
    points[:, 0] /= abs(points[:, 0]) # -1 or 1
    points[:, 1] *= np.pi # 0 <= theta < pi


    # 曲線の順にするためのソート
    # 第1軸(列0)を昇順、その中で第2軸(列1)を昇順
    idx = np.lexsort((points[:, 1], points[:, 0]))
    sorted_arr = points[idx]
    points = sorted_arr

    # Normalize points to lie on the unit sphere
    R = 2
    point_list = []
    for param in points:
      r, theta = param
      x = (R + r * cos(m * theta)) * cos(n * theta)
      y = (R + r * cos(m * theta)) * sin(n * theta)
      z = r * sin(m * theta)

      point = [x, y, z]
      point_list.append(point)

    unit_points = np.array(point_list)

    return unit_points



def generate_unit_sphere_points(n_points: int, seed: int | None = None) -> np.ndarray:
    """Generate points sampled uniformly from the unit sphere."""
    rng = np.random.default_rng(seed)
    points = rng.normal(size=(n_points, 3))
    norms = np.linalg.norm(points, axis=1)
    return points / norms[:, np.newaxis]

def generate_spring_points(n_points: int, coils: float = 5.0, radius: float = 1.0, height: float = 5.0) -> np.ndarray:
    """
    Generates N points representing a spring (helix) shape in 3D.
    
    Args:
        n_points: Number of points to generate.
        coils: Number of coils (turns) of the spring.
        radius: Radius of the spring.
        height: Total height of the spring.
    
    Returns:
        np.ndarray: Array of shape (n_points, 3) containing the generated points.
    """
    t = np.linspace(0, coils * 2 * np.pi, n_points)
    x = radius * np.cos(t)
    y = radius * np.sin(t)
    z = np.linspace(-height / 2, height / 2, n_points)
    
    return np.column_stack((x, y, z))

