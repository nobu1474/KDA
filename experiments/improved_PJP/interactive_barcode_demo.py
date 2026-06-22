import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.generate_point_cloud import generate_spring_points, generate_unit_nm_torus_points
from core.vr_filtration import extract_facet_birth_death_pairs
from visualization.vr_birth_death import plot_birth_death_pairs_by_dimension
from visualization.local_linking_num import plot_local_linking_num_by_dimension
from core.polyline_complex import (
    polylines_from_curve,
    polyline_distance_matrix,
    build_vr_filtration_from_distances,
)

if __name__ == "__main__":
    n=2
    m=3
    # curve = generate_unit_nm_torus_points(500, evenly_spaced=True, n=n, m=m, flatten=False)
    # print(curve)
    curve = generate_unit_nm_torus_points(300, evenly_spaced=False, n=n, m=m)
    # curve = [generate_spring_points(300, coils=15.0, radius=1.0, height=5.0)]
    
    # Webアプリを起動するため、代表して k=5 のみ実行します。
    k = 10
    print(f"\n=== Interactive Polyline Barcode Demo k={k} ===")
    
    polys = []
    for curve_comp in curve:
        polys.extend(polylines_from_curve(curve_comp, k))
        
    print(f"  {len(polys)} polylines, each {len(polys[0])} points")
    
    D = polyline_distance_matrix(polys)
    filtration = build_vr_filtration_from_distances(len(polys), D, max_dimension=3)
    bd_pairs = extract_facet_birth_death_pairs(filtration)
    
    # ファセット(simplex)のインデックスはポリライン(polys)のインデックスに対応するため、
    # 描画用の代表点として各ポリラインの重心(平均座標)を使います。
    # repr_points = [np.mean(p, axis=0) for p in polys]
    
    # plot_birth_death_pairs_by_dimension(
    #     bd_pairs, 
    #     title_prefix=f"Interactive Spring polyline k={k}", 
    #     points=curve,
    #     polylines=polys
    # )

    plot_local_linking_num_by_dimension(
        bd_pairs, 
        title_prefix=f"Interactive Spring polyline k={k}", 
        points=curve,
        polylines=polys
    )
