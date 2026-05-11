import sys
from pathlib import Path
from data.generate_point_cloud import generate_unit_nm_torus_points
from model.knot import Knot
import numpy as np

nmtorus = generate_unit_nm_torus_points(500, n=2, m=4, evenly_spaced=True, flatten=False)
knot = Knot(nmtorus)
knot._ensure_crossings()
crossings = knot._crossings
print(f"Number of crossings: {len(crossings)}")
for c in crossings:
    print(c['sign'])
