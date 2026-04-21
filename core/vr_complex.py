import itertools

import numpy as np


def segment_hausdorff_distance(segment_a, segment_b):
    """Compute Hausdorff distance between two segments represented by point sets."""
    a = np.asarray(segment_a, dtype=float)
    b = np.asarray(segment_b, dtype=float)

    pairwise = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)

    directed_ab = np.max(np.min(pairwise, axis=1))
    directed_ba = np.max(np.min(pairwise, axis=0))
    return float(max(directed_ab, directed_ba))


def distance_matrix(segments):
    """Compute symmetric distance matrix between segments using Hausdorff distance."""
    n = len(segments)
    distances = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            h_dist = segment_hausdorff_distance(segments[i], segments[j])
            distances[i, j] = h_dist
            distances[j, i] = h_dist

    return distances


def build_vietoris_rips_complex(distances, radius, max_dimension=2):
    """Build Vietoris-Rips complex up to max_dimension at a given radius."""
    n = len(distances)
    max_dimension = int(max_dimension)
    if max_dimension < 0:
        raise ValueError("max_dimension must be >= 0")

    simplices = {d: [] for d in range(max_dimension + 1)}

    if max_dimension >= 0:
        for i in range(n):
            simplices[0].append((i,))

    if max_dimension >= 1:
        for i in range(n):
            for j in range(i + 1, n):
                if distances[i, j] <= radius:
                    simplices[1].append((i, j))

    if max_dimension >= 2:
        for i, j, k in itertools.combinations(range(n), 3):
            if (
                distances[i, j] <= radius
                and distances[i, k] <= radius
                and distances[j, k] <= radius
            ):
                simplices[2].append((i, j, k))

    return simplices


def get_facets(simplices, dimension=None):
    """Extract maximal simplices (facets) from a simplicial complex."""
    candidate_by_dim = {
        dim: list(simplices.get(dim, []))
        for dim in sorted(simplices.keys(), reverse=True)
    }

    higher_facet_sets = []
    facets_by_dim = {}

    for dim in sorted(candidate_by_dim.keys(), reverse=True):
        current_candidates = candidate_by_dim[dim]
        if not current_candidates:
            continue

        remaining = []
        for simplex in current_candidates:
            simplex_set = set(simplex)
            if not any(simplex_set.issubset(higher_facet) for higher_facet in higher_facet_sets):
                remaining.append(simplex)

        facets_by_dim[dim] = remaining
        higher_facet_sets.extend([set(simplex) for simplex in remaining])

        remove_by_dim = {}
        for facet in remaining:
            facet_size = len(facet)
            for subset_size in range(1, facet_size):
                remove_dim = subset_size - 1
                remove_by_dim.setdefault(remove_dim, set()).update(
                    itertools.combinations(facet, subset_size)
                )

        for lower_dim, remove_set in remove_by_dim.items():
            if lower_dim not in candidate_by_dim or not candidate_by_dim[lower_dim]:
                continue
            candidate_by_dim[lower_dim] = [
                simplex
                for simplex in candidate_by_dim[lower_dim]
                if simplex not in remove_set
            ]

    facets = []
    for dim in sorted(facets_by_dim.keys(), reverse=True):
        facets.extend(facets_by_dim[dim])

    if dimension is None:
        return facets

    target_size = int(dimension) + 1
    return [facet for facet in facets if len(facet) == target_size]


__all__ = [
    "distance_matrix",
    "build_vietoris_rips_complex",
    "get_facets",
]
