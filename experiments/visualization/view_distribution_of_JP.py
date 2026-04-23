import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.jones import integrated_jones_polynomial
from data.generate_point_cloud import generate_unit_nm_torus_points
from config.constants import N_POINTS, RANDOM_SEED
from visualization.jones_distribution import (
    plot_distinct_jones_poly_diagrams,
    plot_poly_map_on_sphere,
)


if __name__ == "__main__":
    # config = load_experiment_config(PROJECT_ROOT / "config" / "experiment_default.json")

    # if config.shape == "nm_torus":
    #     curves = [
    #         generate_unit_nm_torus_points(
    #             n_points=config.n_points,
    #             n=config.torus_n,
    #             m=config.torus_m,
    #             seed=config.random_seed,
    #         )
    #     ]
    # else:
    #     raise ValueError(f"Unsupported shape for distribution experiment: {config.shape}")


    nmtorus_points_3d = generate_unit_nm_torus_points(N_POINTS, seed=RANDOM_SEED)
    curves = [nmtorus_points_3d]
    poly_map = integrated_jones_polynomial(curves, Number_of_projections=10, RANDOM_SEED=RANDOM_SEED,show_progress=True)

    plot_poly_map_on_sphere(poly_map)

    # 異なるJones多項式ごとに2D図式を表示
    plot_distinct_jones_poly_diagrams(curves, poly_map)
