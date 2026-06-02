import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.open_curve_jones import open_curve_jones_polynomial
from functions import generate_unit_sphere_points, launch_interactive_jones_direction_explorer

if __name__ == "__main__":
    # experiments/open_curve_JP/cross.py で定義された曲線データを使用
    curve1 = np.array([
        [1, 1, 1],
        [-1, 1, -1]
    ], dtype=float)
    
    curve2 = np.array([
        [-1, -1, 1],
        [1, -1, -1]
    ], dtype=float)
    
    curves = [curve1, curve2]

    # 球面上の射影方向ベクトルを1000個サンプリング
    number_of_projections = 1000
    random_seed = 42
    sphere_points = generate_unit_sphere_points(number_of_projections, seed=random_seed)

    print(f"[{number_of_projections}個の方向に対する開曲線のJones多項式を計算します...]")
    poly_map = {}
    
    for i, proj_vec in enumerate(sphere_points):
        if i % 100 == 0:
            print(f" Progress: {i}/{number_of_projections}")
        
        # 今回作成した開曲線用ジョーンズ多項式関数を使って計算
        jp = open_curve_jones_polynomial(curves, projection_vector=proj_vec)
        poly_map[tuple(proj_vec)] = jp

    print("計算完了！インタラクティブビューワを起動します...")

    # 計算したpoly_mapをそのまま既存のエクスプローラーに投げる
    launch_interactive_jones_direction_explorer(
        curves=curves,
        poly_map=poly_map,
        title="Open Curve Jones Polynomial Explorer",
        host="127.0.0.1",
        port=8050,
        debug=False,
        run_server=True,
    )