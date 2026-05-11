try:
    from config.constants import N_POINTS, RANDOM_SEED
except:
    N_POINTS, RANDOM_SEED = 500, 42
from model.knot import Knot
from data.generate_point_cloud import generate_unit_nm_torus_points
for m in [2, 4, 6]:
    nmtorus = generate_unit_nm_torus_points(N_POINTS, n=2, m=m, seed=RANDOM_SEED, evenly_spaced=False, flatten=False)
    knot = Knot(nmtorus)
    knot._ensure_writhe()
    print(f"m={m}, evenly_spaced=False, crossings: {len(knot.crossings)}, writhe: {knot._writhe}")
    print(f"  {knot.jones_polynomial_str}")
