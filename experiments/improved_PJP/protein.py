import sys
from pathlib import Path
import numpy as np
import time

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vr_filtration import extract_facet_birth_death_pairs
from visualization.vr_birth_death import plot_birth_death_pairs_by_dimension
from visualization.point_cloud import plot_3d_point_cloud
from core.polyline_complex import (
    polylines_from_curve,
    polyline_distance_matrix,
    build_vr_filtration_from_distances,
)

# 設定
data_file = 'data/protein_data/sample_conformations.npz'
elements_file = 'data/protein_data/elements_array.txt'

if __name__ == "__main__":
    data = np.load(data_file)['arr_0'].astype('float64')
    # num_samples = data.shape[0]
    
    num = 0
    # curve = [data[1]]
    curve = [data[num][0:300]]
    # plot_3d_point_cloud(curve[0], title="Protein Conformation Sample")
    
    start_time = time.time()
    # Webアプリを起動するため、代表して k=5 のみ実行します。
    k = 2
    print(f"\n=== Interactive Polyline Barcode Demo k={k} ===")
    
    polys = []
    for curve_comp in curve:
        polys.extend(polylines_from_curve(curve_comp, k))
        
    print(f"  {len(polys)} polylines, each {len(polys[0])} points")
    
    D = polyline_distance_matrix(polys)
    filtration = build_vr_filtration_from_distances(len(polys), D, max_dimension=3)
    bd_pairs = extract_facet_birth_death_pairs(filtration)
    
    
    plot_birth_death_pairs_by_dimension(
        bd_pairs, 
        title_prefix=f"Protein Data{num} k={k}", 
        points=curve,
        polylines=polys
    )
    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_hour = elapsed_time // 3600
    elapsed_minute = (elapsed_time % 3600) // 60
    elapsed_second = (elapsed_time % 3600 % 60)
    print(f"Total time: {str(elapsed_hour).zfill(2)}:{str(elapsed_minute).zfill(2)}:{str(elapsed_second).zfill(2)}")