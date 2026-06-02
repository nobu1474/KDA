import numpy as np
from core.crossings import find_crossings
from core.open_curve_jones import count_open_curve_state_cycles_by_orbits, open_curve_kauffman_bracket
from functions import generate_states

curve1 = np.array([[1, 1, 1], [-1, 1, -1]], dtype=float)
curve2 = np.array([[-1, -1, 1], [1, -1, -1]], dtype=float)
curves = [curve1, curve2]
crossings = find_crossings(curves, projection_vector=np.array([0, 1, 0]))

print("Crossings:", len(crossings))
for c in crossings:
    print(c)
    
states = generate_states(len(crossings))
for state in states:
    c = count_open_curve_state_cycles_by_orbits(crossings, state, len(curves))
    print(f"State {state}: components = {c}")
