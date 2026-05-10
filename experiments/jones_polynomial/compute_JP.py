import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.generate_point_cloud import generate_unit_nm_torus_points
from visualization.point_cloud import plot_3d_point_cloud
from config.constants import N_POINTS, RANDOM_SEED
from model.knot import Knot


if __name__ == "__main__":
    # ===== Test Jones Polynomial Calculation =====

    n=2
    m=5
    print("\n" + "="*60)
    print("Testing Jones Polynomial Calculation")
    print("="*60)

    nmtorus_points_3d = generate_unit_nm_torus_points(N_POINTS, n=n, m=m, seed=RANDOM_SEED, flatten=False)
    # plot_3d_point_cloud(nmtorus_points_3d, title=f"({n},{m})-Torus Points", equal_aspect=True)
    # nmtorus_points_3d is now a list of curves for the link components
    curves = nmtorus_points_3d
    # Test 1: Calculate Jones polynomial for the (n,m)-torus knot
    knot = Knot(curves)
    print(f"\nNumber of crossings: {len(knot.crossings)}")
    print(f"\nJones polynomial (bracket form):")
    print(f"  Raw dict: {knot.jones_polynomial}")
    print(f"\nFormatted: {knot.jones_polynomial_str}")
