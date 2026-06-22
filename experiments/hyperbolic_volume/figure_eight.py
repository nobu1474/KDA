import sys
from pathlib import Path
from snappy import Manifold, Link

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))
	
from data.generate_point_cloud import generate_unit_Figure_eight_knot_points, generate_unit_nm_torus_points
from visualization.point_cloud import plot_3d_point_cloud

if __name__ == "__main__":
    # 3D Figure-eight knotの点群を生成
    # num_points = 500
    # curve = generate_unit_Figure_eight_knot_points(num_points, evenly_spaced=True, flatten=False)
    
    # # 生成した点群を可視化
    # plot_3d_point_cloud(curve[0], title=f"3D Figure-eight Knot with {num_points} Points", equal_aspect=True)

    # L = Link(curve[0])

    pd = [(1,6,2,5),
      (3,8,4,7),
      (5,2,6,1)]
    
    L = Link(pd)

    # 3. 結び目の補空間（多様体）に変換
    M = L.exterior()

    # 4. 双曲体積を計算して出力
    volume = M.volume()
    print(f"計算された双曲体積: {volume}")
