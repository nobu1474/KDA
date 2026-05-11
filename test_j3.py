from model.knot import Knot
from data.generate_point_cloud import generate_unit_nm_torus_points
for m in [2, 4, 6]:
    nmtorus = generate_unit_nm_torus_points(500, n=2, m=m, evenly_spaced=True, flatten=False)
    knot = Knot(nmtorus)
    knot._ensure_writhe()
    print(f"m={m}, crossings: {len(knot.crossings)}, writhe: {knot._writhe}")
    print(f"  {knot.jones_polynomial_str}")
