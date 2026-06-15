import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vr_filtration import extract_facet_birth_death_pairs
from core.open_curve_jones import open_curve_crossing_info
from core.polyline_complex import (
    polylines_from_curve,
    polyline_distance_matrix,
    build_vr_filtration_from_distances,
)
from visualization.vr_birth_death import facet_to_curves

# 設定
data_file = 'data/protein_data/sample_conformations.npz'
elements_file = 'data/protein_data/elements_array.txt'

if __name__ == "__main__":
    data = np.load(data_file)['arr_0'].astype('float64')
    # num_samples = data.shape[0]
    
    curve = [data[0]]
    
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

    max_crossing_num = 0
    for dim in range(len(bd_pairs)-1):  # 最後の次元は∞ペアなので除外
        print(f"Dimension {dim}:")
        for pair in bd_pairs[dim]:
            polys = facet_to_curves(pair, polys)
            crossing_info, crossing_nums = open_curve_crossing_info(polys)
            if max(crossing_nums) > max_crossing_num:
                max_crossing_num = max(crossing_nums)


    print(f"Max crossing number across all pairs: {max_crossing_num}")