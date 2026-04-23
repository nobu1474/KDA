"""Jones polynomial and related algebra.

This module currently re-exports logic from functions.py so existing
behavior is preserved while enabling a cleaner package structure.
"""

from functions import (
    _convert_A_poly_to_t_poly,
    _normalize_bracket_to_jones_in_A,
    apply_smoothing,
    format_jones_polynomial,
    generate_states,
    integrated_jones_polynomial,
    jones_polynomial,
    kauffman_bracket,
    laurent_add,
    laurent_mul,
    laurent_pow,
    launch_interactive_jones_direction_explorer,
)

__all__ = [
    "laurent_add",
    "laurent_mul",
    "laurent_pow",
    "generate_states",
    "apply_smoothing",
    "kauffman_bracket",
    "jones_polynomial",
    "integrated_jones_polynomial",
    "launch_interactive_jones_direction_explorer",
    "format_jones_polynomial",
    "_normalize_bracket_to_jones_in_A",
    "_convert_A_poly_to_t_poly",
]
