"""Shared constants used across experiments.

This module centralizes values that were previously defined near the top
of main.py.
"""

# Defaults for quick experiments
N_POINTS = 500
RANDOM_SEED = 42

# Labels
sphere = "Sphere"
nm_torus = "(n,m)-torus knot"
torus = "Torus"
mobius_band = "Mobius band"

# Optional uppercase aliases for future code
SPHERE = sphere
NM_TORUS = nm_torus
TORUS = torus
MOBIUS_BAND = mobius_band

__all__ = [
    "N_POINTS",
    "RANDOM_SEED",
    "sphere",
    "nm_torus",
    "torus",
    "mobius_band",
    "SPHERE",
    "NM_TORUS",
    "TORUS",
    "MOBIUS_BAND",
]
