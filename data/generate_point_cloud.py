from math import cos, sin

import numpy as np



import math

def generate_unit_nm_torus_points(n_points, n=2, m=3,seed=None, evenly_spaced=False, flatten=True):
    """Generates N points sampled on a unit (n,m)-torus in 3D."""
    if seed is not None:
        np.random.seed(seed)

    R = 2
    d = math.gcd(n, m)
    n_prime = n // d
    m_prime = m // d

    points_per_comp = n_points // d
    remainder = n_points % d

    unit_points = []
    
    for k in range(d):
        num_points = points_per_comp + (1 if k < remainder else 0)
        if num_points == 0:
            continue
            
        if evenly_spaced:
            # パラメータtを[0, 2π)で等間隔に生成する
            t = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
        else:
            # パラメータtを[0, 2π)の範囲でランダムサンプリングし、曲線順になるようソートする
            t = np.random.rand(num_points) * 2 * np.pi
            t = np.sort(t)

        phi = n_prime * t
        theta = m_prime * t + (2 * np.pi * k / d)

        x = (R + np.cos(theta)) * np.cos(phi)
        y = (R + np.cos(theta)) * np.sin(phi)
        z = np.sin(theta)
        
        comp_points = np.column_stack((x, y, z))
        unit_points.append(comp_points)
        
    if flatten:
        return np.vstack(unit_points)
    # トーラス結び目・絡み目の各成分をそのままリストとして返す
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

def generate_circle_points(n_points: int, seed: int | None = None, evenly_spaced: bool = False) -> np.ndarray:
    """Generate points sampled uniformly from the unit circle.
    
    Args:
        n_points: Number of points to generate.
        seed: Random seed.
        evenly_spaced: If True, generates points evenly spaced along the circle instead of random normal points.
    """
    if evenly_spaced:
        theta = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
        x = np.cos(theta)
        y = np.sin(theta)
        z = np.zeros(n_points)
        return np.column_stack((x, y, z))

    rng = np.random.default_rng(seed)
    points = rng.normal(size=(n_points, 3))
    for i in range(points.shape[0]):
        points[i, 2] = 0  # z座標を0に固定して円を形成
    norms = np.linalg.norm(points, axis=1)
    points = points / norms[:, np.newaxis]
    
    # 円の曲線に沿った順序になるように角度でソート
    angles = np.arctan2(points[:, 1], points[:, 0])
    sort_indices = np.argsort(angles)
    return points[sort_indices]

def generate_line_points(n_points: int, seed: int | None = None, evenly_spaced: bool = False, n_lines: int = 1) -> np.ndarray:
    """Generate points sampled uniformly from a line segment.
    
    Args:
        n_points: Total number of points to generate.
        seed: Random seed.
        evenly_spaced: If True, generates points evenly spaced along the line(s).
        n_lines: Number of parallel line segments to generate.
    """
    rng = np.random.default_rng(seed)
    points_per_line = n_points // n_lines
    all_points = []
    
    for line_idx in range(n_lines):
        # 複数本の場合は y 座標をずらして平行な線分にする
        y_val = (line_idx - (n_lines - 1) / 2.0) if n_lines > 1 else 0.0
        
        if evenly_spaced:
            x_vals = np.linspace(-1, 1, points_per_line)
        else:
            x_vals = rng.normal(size=points_per_line)
            
        y_vals = np.full(points_per_line, y_val)
        z_vals = np.zeros(points_per_line)
        
        all_points.append(np.column_stack((x_vals, y_vals, z_vals)))
        
    points = np.vstack(all_points)
    
    # 割り切れなかった分の端数処理 (余りの点は最初の線分に追加)
    remainder = n_points - len(points)
    if remainder > 0:
        if evenly_spaced:
            extra_x = np.linspace(-1, 1, remainder)
        else:
            extra_x = rng.normal(size=remainder)
        y_val = (0 - (n_lines - 1) / 2.0) if n_lines > 1 else 0.0
        extra_pts = np.column_stack((extra_x, np.full(remainder, y_val), np.zeros(remainder)))
        points = np.vstack((points, extra_pts))
        
    return points