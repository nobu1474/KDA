"""Vietoris-Rips filtration helpers and persistence utilities."""

from core.vr_complex import build_vietoris_rips_complex, distance_matrix, get_facets

from functions import (
    build_simplex_birth_time_map,
    build_vr_filtration,
    build_vr_persistence_with_homcloud,
    compute_critical_values,
    extract_barcode_from_filtration,
    extract_facet_birth_death_pairs,
    extract_facet_presence_from_filtration,
    pairwise_distance_matrix,
    plot_birth_death_pairs_by_dimension,
    print_vr_filtration_summary,
    segment_hausdorff_distance,
    segment_midpoints,
)

__all__ = [
    "segment_hausdorff_distance",
    "distance_matrix",
    "build_vietoris_rips_complex",
    "get_facets",
    "compute_critical_values",
    "build_vr_filtration",
    "build_simplex_birth_time_map",
    "extract_facet_birth_death_pairs",
    "extract_facet_presence_from_filtration",
    "extract_barcode_from_filtration",
    "plot_birth_death_pairs_by_dimension",
    "print_vr_filtration_summary",
    "segment_midpoints",
    "pairwise_distance_matrix",
    "build_vr_persistence_with_homcloud",
]
