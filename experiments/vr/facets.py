import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.generate_point_cloud import generate_unit_nm_torus_points
from config.constants import N_POINTS, RANDOM_SEED
from core.vr_filtration import build_vietoris_rips_complex, distance_matrix, get_facets


if __name__ == "__main__":
    """単体複体のfacet"""
    triangle_1 = {0:[(0,),(1,),(2,)], 1:[(0, 1),(1, 2),(2, 0)], 2:[(0, 1, 2)]}
    triangle_2 = {0:[(0,),(1,),(2,)], 1:[(0, 1),(1, 2),(2, 0)], 2:[]}
    triangle_3 = {0:[(0,),(1,),(2,),(3,),(4,),(5,),(6,)], 1:[(0, 1),(1, 2),(2, 0),(0, 3),(4, 3),(4, 0)], 2:[(0, 1, 2)]}

    print(get_facets(triangle_1))
    print(get_facets(triangle_2))
    print(get_facets(triangle_3))


    """フィルトレーションのある時刻の単体複体のfacet"""
    curve = generate_unit_nm_torus_points(N_POINTS, seed=RANDOM_SEED)
    segments = [curve[i:i + 2] for i in range(len(curve) - 1)]
    distances = distance_matrix(segments)
    complexes = build_vietoris_rips_complex(distances, 2)
    facets = get_facets(complexes)
    print(facets)
