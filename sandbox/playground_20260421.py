"""Temporary scratch file for experiments.

Guideline:
- Keep short trial code here instead of commenting large blocks in main scripts.
- Move stable logic to core/, data/, model/, or app/ once validated.
"""

from core.jones import format_jones_polynomial
from data.generate_point_cloud import generate_unit_nm_torus_points
from model.knot import Knot


if __name__ == "__main__":
    curve = generate_unit_nm_torus_points(n_points=300, seed=42)
    knot = Knot([curve])

    print("crossings:", len(knot.crossings))
    print("writhe:", knot.writhe)
    print("jones:", format_jones_polynomial(knot.jones_polynomial))
