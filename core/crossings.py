"""Crossing and projection helpers.

This module is a thin layer around stable functions in functions.py.
It provides clearer import boundaries for new code.
"""

from functions import (
    crossing_number_distribution,
    crossing_over_under,
    crossing_sign,
    find_crossings,
    generate_unit_sphere_points,
    orient,
    plot_crossing_num_map_on_sphere,
    orthonormal_basis,
    project_to_2D,
    segment_intersection_params,
    segments_intersect_2d,
)

__all__ = [
    "orient",
    "segments_intersect_2d",
    "segment_intersection_params",
    "crossing_over_under",
    "crossing_sign",
    "crossing_number_distribution",
    "find_crossings",
    "orthonormal_basis",
    "plot_crossing_num_map_on_sphere",
    "project_to_2D",
    "generate_unit_sphere_points",
]
