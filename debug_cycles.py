import sys
from pathlib import Path
from data.generate_point_cloud import generate_unit_nm_torus_points
from core.crossings import find_crossings
from functions import generate_states, sigma, count_state_cycles_by_orbits
import numpy as np

curves = generate_unit_nm_torus_points(500, n=2, m=4, evenly_spaced=True, flatten=False)
crossings = find_crossings(curves)
print(f"Number of crossings: {len(crossings)}")

for state in generate_states(len(crossings)):
    cycle_count = count_state_cycles_by_orbits(crossings, state)
    print(f"State {state} (sigma={sigma(state)}): count={cycle_count}, parity={(sigma(state) + 2*(cycle_count-1)) % 4}")
