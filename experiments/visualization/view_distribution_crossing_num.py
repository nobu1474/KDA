import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.constants import N_POINTS, RANDOM_SEED
from core.crossings import crossing_number_distribution
from data.generate_point_cloud import generate_unit_nm_torus_points
from visualization.crossing_distribution import plot_crossing_num_map_on_sphere


if __name__ == "__main__":
    nmtorus_points_3d = generate_unit_nm_torus_points(N_POINTS, seed=RANDOM_SEED)
    curves = [nmtorus_points_3d]

    crossing_num_map = crossing_number_distribution(
        curves,
        Number_of_projections=10000,
        RANDOM_SEED=RANDOM_SEED,
        show_progress=True,
    )

    plot_crossing_num_map_on_sphere(crossing_num_map)
