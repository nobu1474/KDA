import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.open_curve_jones import open_curve_jones_polynomial
from functions import format_jones_polynomial
from visualization.point_cloud import plot_3d_point_cloud

if __name__ == "__main__":
    # テスト用の開曲線を定義
    # まずは簡単な2成分からなる開曲線など
    # 交差を作るためにねじれた直線を2本用意する
    curve1 = np.array([
        [1, 1, 1],
        [-1, 1, -1]
    ], dtype=float)
    
    curve2 = np.array([
        [-1, -1, 1],
        [1, -1, -1]
    ], dtype=float)
    
    curves = [curve1, curve2]
    # plot_3d_point_cloud(curves, title="Curve 1", equal_aspect=True)
    
    print("Computing Jones polynomial for the open curves...")
    jp_x = open_curve_jones_polynomial(curves, projection_vector=np.array([1, 0, 0]))
    jp_y = open_curve_jones_polynomial(curves, projection_vector=np.array([0, 1, 0]))
    jp_z = open_curve_jones_polynomial(curves, projection_vector=np.array([0, 0, 1]))
    
    print(f"Jones Polynomial (X): {format_jones_polynomial(jp_x)}")
    print(f"Jones Polynomial (Y): {format_jones_polynomial(jp_y)}")
    print(f"Jones Polynomial (Z): {format_jones_polynomial(jp_z)}")

