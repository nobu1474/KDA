import numpy as np
import plotly.graph_objects as go
from math import pi, cos, sin

# --- Configuration ---
N_POINTS = 500  # Number of points in the 3D point cloud
RANDOM_SEED = 42 # Fixed random seed for reproducibility

sphere = "Sphere"
nm_torus = "(n,m)-torus knot"
torus = "Torus"
mobius_band = "Mobius band"


def make_linked_circles(n=100):
    t = np.linspace(0, 2*np.pi, n)

    # xy平面の円
    circle1 = np.stack([
        np.cos(t),
        np.sin(t),
        np.zeros_like(t)
    ], axis=1)

    # yz平面の円（少しずらす）
    circle2 = np.stack([
        np.zeros_like(t) + 0.5,
        np.cos(t),
        np.sin(t)
    ], axis=1)

    return [circle1, circle2]

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


def generate_unit_sphere_points(n_points, seed=None):
    """Generates N points uniformly sampled on a unit sphere in 3D."""
    if seed is not None:
        np.random.seed(seed)

    # Generate random points in 3D space
    points = np.random.randn(n_points, 3)

    # Normalize points to lie on the unit sphere
    norms = np.linalg.norm(points, axis=1)
    unit_points = points / norms[:, np.newaxis]
    return unit_points




# curves = make_linked_circles()
# endpoints = [
#     (curve[0], curve[-1])
#     for curve in curves
# ]





def plot_3d_point_cloud(points, title="Sphere"):
    """Plots a 3D scatter plot of the given points."""
    fig = go.Figure(data=[go.Scatter3d(
        x=points[:, 0],
        y=points[:, 1],
        z=points[:, 2],
        mode='markers',
        marker=dict(
            size=3,
            color=points[:, 2], # Color by Z-coordinate for visual effect
            colorscale='Viridis',
            opacity=0.8
        )
    )])

    fig.update_layout(
        title=f"3D Point Cloud on Unit {title}",
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='cube' # Ensures equal scaling for axes
        )
    )
    fig.show()

def plot_2d_point_cloud(points, title="Projection"):
    """Plots a 2D scatter plot of the given points."""
    fig = go.Figure(data=[go.Scatter(
        x=points[:, 0],
        y=points[:, 1],
        mode='markers',
        marker=dict(
            size=6,
            color=points[:, 1],
            colorscale='Viridis',
            opacity=0.85
        )
    )])

    fig.update_layout(
        title=f"2D Point Cloud on {title}",
        xaxis_title='X',
        yaxis_title='Y',
        yaxis_scaleanchor='x',
        yaxis_scaleratio=1
    )
    fig.show()

# plot_3d_point_cloud(curves[0], title="Circle 1 (XY Plane)")
# plot_3d_point_cloud(curves[1], title="Circle 2 (YZ Plane)")

# linkoid = curves[0][:, :2]  # Z方向へ射影して (x, y) の2軸だけを取り出す
# plot_2d_point_cloud(linkoid, title="Circle 1 (XY Projection)")

# plot_3d_point_cloud(nmtorus_points_3d, title=nm_torus)
# linkoid = nmtorus_points_3d[:, :2]  # Z方向へ射影して (x, y) の2軸だけを取り出す
# plot_2d_point_cloud(linkoid, title=f"{nm_torus} Projection")

nmtorus_points_3d = generate_unit_nm_torus_points(N_POINTS, seed=RANDOM_SEED)
# sphere_points = generate_unit_sphere_points(5,RANDOM_SEED)
# linkoid_x = nmtorus_points_3d[:, [1, 2]]
# linkoid_y = nmtorus_points_3d[:, [0, 2]]
# linkoid_z = nmtorus_points_3d[:, [0, 1]]
# plot_2d_point_cloud(linkoid_x, title=f"{nm_torus} X-Projection")
# plot_2d_point_cloud(linkoid_y, title=f"{nm_torus} Y-Projection")
# plot_2d_point_cloud(linkoid_z, title=f"{nm_torus} Z-Projection")

# plot_3d_point_cloud(nmtorus_points_3d, title=nm_torus)



# import matplotlib.pyplot as plt
# def plot_curves(curve):
#     fig = plt.figure()
#     ax = fig.add_subplot(projection='3d')

#     ax.plot(curve[:,0], curve[:,1], curve[:,2])

#     plt.show()

# plot_curves(nmtorus_points_3d)

from functions import find_crossings
crossings = find_crossings([nmtorus_points_3d])
# print(crossings)

# nmtorus_points_3d の交点の結果
# {'segments': (45, 293), 't': np.float64(0.3053375527175949), 's': np.float64(0.5039362912248272), 'over': 'q_over', 'sign': 1}, 
# {'segments': (126, 375), 't': np.float64(0.36192802334), 's': np.float64(0.4473185255595932), 'over': 'p_over', 'sign': -1}, 
# {'segments': (213, 459), 't': np.float64(0.870320966722455), 's': np.float64(0.4019840746846808), 'over': 'q_over', 'sign': 1}

# 修正版　こっちが正しい結果
[{'segments': (45, 293), 't': np.float64(0.3053375527175949), 's': np.float64(0.5039362912248272), 'over': 'q_over', 'sign': -1}, 
 {'segments': (126, 375), 't': np.float64(0.36192802334), 's': np.float64(0.4473185255595932), 'over': 'p_over', 'sign': -1}, 
 {'segments': (213, 459), 't': np.float64(0.870320966722455), 's': np.float64(0.4019840746846808), 'over': 'q_over', 'sign': -1}]


from functions import apply_smoothing, generate_states
states = generate_states(len(crossings))

labeled_crossings = apply_smoothing(crossings, states[0])
# print(labeled_crossings)







# ===== Test Jones Polynomial Calculation =====
from functions import jones_polynomial, format_jones_polynomial

print("\n" + "="*60)
print("Testing Jones Polynomial Calculation")
print("="*60)

curves = [nmtorus_points_3d]
# Test 1: Calculate Jones polynomial for the (n,m)-torus knot
jp = jones_polynomial(curves)
print(f"\nNumber of crossings: {len(crossings)}")
print(f"\nJones polynomial (bracket form):")
print(f"  Raw dict: {jp}")
print(f"\nFormatted: {format_jones_polynomial(jp)}")

print("\n" + "-"*60)
from functions import integrated_jones_polynomial, plot_poly_map_on_sphere, plot_distinct_jones_poly_diagrams

import time
start = time.perf_counter() #計測開始

poly_map = integrated_jones_polynomial(curves)

end = time.perf_counter() #計測終了
print(f"{(end - start)//60} 分 {(end - start)%60} 秒") #計測結果を表示

print(f"\nProjection -> Jones polynomial map:")
print(f"  Number of projection directions: {len(poly_map)}")
print(f"  Number of distinct polynomials: {len({tuple(sorted(v.items(), key=lambda item: str(item[0]))) for v in poly_map.values()})}")


# 可視化のための人たち
# plot_poly_map_on_sphere(poly_map, title="Jones polynomial classes by projection direction")

# 異なるJones多項式ごとに2D図式を表示
# plot_distinct_jones_poly_diagrams([nmtorus_points_3d], poly_map)


# 射影方向を変えてみる
# import math
# vector_x = np.array([1, 0, 0]) # X軸方向
# vector_y = np.array([0, 1, 0]) # Y軸方向
# vector_z = np.array([0, 0, 1]) # Z軸方向
# vector_a = np.array([1/math.sqrt(3), 1/math.sqrt(3), 1/math.sqrt(3)]) # (1,1,1)方向
# print(jones_polynomial([nmtorus_points_3d],vector_x)) # こいつだけ変な多項式
# print(jones_polynomial([nmtorus_points_3d],vector_y))
# print(jones_polynomial([nmtorus_points_3d],vector_z))
# print(jones_polynomial([nmtorus_points_3d],vector_a))

# from functions import project_to_2D
# diagram_z = project_to_2D(nmtorus_points_3d, vector_a)

# plot_2d_point_cloud(diagram_z, title=f"{nm_torus} Z-Projection")




"""
persistent Jonres polynomial を作っていきたい
TODO: そのための曲線の集合のデータを作る。良いデータの作り方は何かないか
"""


