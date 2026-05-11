import sys
from pathlib import Path
from model.knot import Knot
from data.generate_point_cloud import generate_unit_nm_torus_points

nmtorus = generate_unit_nm_torus_points(500, n=2, m=4, evenly_spaced=True, flatten=False)
knot = Knot(nmtorus)
knot._ensure_writhe()
print(f"Number of crossings: {len(knot.crossings)}")
print(f"Writhe: {knot._writhe}")
print(f"Raw dict: {knot.jones_polynomial}")
print(f"Formatted: {knot.jones_polynomial_str}")
