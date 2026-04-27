import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vr_filtration import build_vr_filtration, extract_facet_birth_death_pairs
from data.generate_point_cloud import generate_unit_nm_torus_points
from visualization.vr_birth_death import plot_birth_death_pairs_by_dimension
from config.constants import N_POINTS, RANDOM_SEED


if __name__ == "__main__":
    curve = generate_unit_nm_torus_points(50, seed=RANDOM_SEED)
    segments = [curve[i:i + 2] for i in range(len(curve) - 1)]

    filtration = build_vr_filtration(segments)
    bd_pair = extract_facet_birth_death_pairs(filtration)

    for dim, pairs in bd_pair.items():
        print(f"dimension={dim}, n_pairs={len(pairs)}")
        for pair in pairs[:5]:
            print(pair)

    plot_birth_death_pairs_by_dimension(bd_pair)
    