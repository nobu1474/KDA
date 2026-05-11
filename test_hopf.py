from model.knot import Knot
from data.generate_point_cloud import generate_unit_nm_torus_points
nmtorus = generate_unit_nm_torus_points(500, n=2, m=2, evenly_spaced=True, flatten=False)
knot = Knot(nmtorus)
knot._ensure_writhe()
print(knot.jones_polynomial_str)
