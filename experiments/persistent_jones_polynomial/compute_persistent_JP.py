import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vr_filtration import build_vr_filtration, extract_facet_birth_death_pairs
from data.generate_point_cloud import generate_unit_nm_torus_points
from visualization.vr_birth_death import plot_birth_death_pairs_by_dimension
from config.constants import N_POINTS, RANDOM_SEED
from visualization.point_cloud import plot_3d_point_cloud
from core.persistent_jones import plot_persistent_jones_polynomial


if __name__ == "__main__":
    curve = generate_unit_nm_torus_points(50, seed=RANDOM_SEED)
    # plot_3d_point_cloud(curve, title="Unit Nm Torus")
    segments = [curve[i:i + 2] for i in range(len(curve) - 1)]

    filtration = build_vr_filtration(segments, max_dimension = 3)
    bd_pair = extract_facet_birth_death_pairs(filtration)
    
    # 5.2節のPersistent Jones Polynomialの図を描画
    plot_persistent_jones_polynomial(curve, filtration, bd_pair)
