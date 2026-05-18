import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from data.generate_point_cloud import generate_unit_nm_torus_points
from core.vr_filtration import extract_facet_birth_death_pairs
from visualization.vr_birth_death import plot_birth_death_pairs_by_dimension
from core.polyline_complex import (
    polylines_from_curve,
    polyline_distance_matrix,
    _build_vr_filtration_from_distances,
)

if __name__ == "__main__":
    curve = generate_unit_nm_torus_points(100, evenly_spaced=True, n=2, m=3)
    # k=1 → 99 polylines, k=2 → 49, k=5 → 19
    for k in [1, 2, 5]:
        print(f"\n=== k={k} ===")
        polys = polylines_from_curve(curve, k)
        print(f"  {len(polys)} polylines, each {len(polys[0])} points")
        D = polyline_distance_matrix(polys)
        filtration = _build_vr_filtration_from_distances(len(polys), D, max_dimension=2)
        bd_pairs = extract_facet_birth_death_pairs(filtration)
        plot_birth_death_pairs_by_dimension(bd_pairs, title_prefix=f"nm-torus polyline k={k}")
