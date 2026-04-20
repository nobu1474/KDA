import time
import numpy as np
from math import cos, sin
from functions import distance_matrix, build_vietoris_rips_complex, get_facets

N_POINTS = 500
RANDOM_SEED = 42
RADIUS = 3.0
MAX_DIMENSION = 2


def generate_unit_nm_torus_points(n_points, n=2, m=3, seed=None):
    if seed is not None:
        np.random.seed(seed)

    points = np.random.rand(n_points, 2)
    points[:, 0] *= 2
    points[:, 0] -= 1
    points[:, 0] /= abs(points[:, 0])
    points[:, 1] *= np.pi

    idx = np.lexsort((points[:, 1], points[:, 0]))
    points = points[idx]

    R = 2
    point_list = []
    for r, theta in points:
        x = (R + r * cos(m * theta)) * cos(n * theta)
        y = (R + r * cos(m * theta)) * sin(n * theta)
        z = r * sin(m * theta)
        point_list.append([x, y, z])

    return np.array(point_list)


def old_get_facets(simplices, dimension=None):
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
        higher_facet_sets.extend(set(simplex) for simplex in remaining)

    facets = []
    for dim in sorted(facets_by_dim.keys(), reverse=True):
        facets.extend(facets_by_dim[dim])

    if dimension is None:
        return facets

    target_size = int(dimension) + 1
    return [facet for facet in facets if len(facet) == target_size]


def main():
    t0 = time.perf_counter()
    points = generate_unit_nm_torus_points(N_POINTS, seed=RANDOM_SEED)
    segments = [points[i:i + 2] for i in range(len(points) - 1)]
    t1 = time.perf_counter()

    distances = distance_matrix(segments)
    t2 = time.perf_counter()

    simplices = build_vietoris_rips_complex(distances, radius=RADIUS, max_dimension=MAX_DIMENSION)
    t3 = time.perf_counter()

    old_start = time.perf_counter()
    old_facets = old_get_facets(simplices)
    old_end = time.perf_counter()

    new_start = time.perf_counter()
    new_facets = get_facets(simplices)
    new_end = time.perf_counter()

    if sorted(old_facets) != sorted(new_facets):
        raise RuntimeError("facet outputs differ on real data")

    old_s = old_end - old_start
    new_s = new_end - new_start
    speedup = old_s / new_s if new_s > 0 else float("inf")

    print("=== Real Data Facet Benchmark ===")
    print(f"N_POINTS={N_POINTS}, segments={len(segments)}, radius={RADIUS}, max_dimension={MAX_DIMENSION}")
    print(f"prep_points_segments={t1 - t0:.3f}s")
    print(f"distance_matrix={t2 - t1:.3f}s")
    print(f"build_complex={t3 - t2:.3f}s")
    print(f"|S0|={len(simplices.get(0, []))}, |S1|={len(simplices.get(1, []))}, |S2|={len(simplices.get(2, []))}")
    print(f"old_get_facets={old_s:.6f}s")
    print(f"new_get_facets={new_s:.6f}s")
    print(f"speedup={speedup:.2f}x")


if __name__ == "__main__":
    main()
