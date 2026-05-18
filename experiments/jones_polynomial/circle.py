import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.generate_point_cloud import generate_circle_points
from config.constants import N_POINTS, RANDOM_SEED
from model.knot import Knot
from visualization.point_cloud import plot_3d_point_cloud


if __name__ == "__main__":
    # ===== Test Jones Polynomial Calculation =====

    print("\n" + "="*60)
    print("Testing Jones Polynomial Calculation")
    print("="*60)

    n_point = 100
    circle_points = generate_circle_points(n_point, seed=RANDOM_SEED)
    curves = [circle_points]
    # plot_3d_point_cloud(curves, title=f"Circle Points ({n_point} points)", equal_aspect=True)

    # Test 1: Calculate Jones polynomial for the (n,m)-torus knot
    knot = Knot(curves)
    print(f"\nNumber of crossings: {len(knot.crossings)}")
    print(f"\nJones polynomial (bracket form):")
    print(f"  Raw dict: {knot.jones_polynomial}")
    print(f"\nFormatted: {knot.jones_polynomial_str}")