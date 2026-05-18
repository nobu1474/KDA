"""Polyline-based Vietoris-Rips filtration using exact arc-arc Hausdorff distance."""

import itertools

import numpy as np


def point_to_segment_distance(p, a, b) -> float:
    """Exact distance from point p to segment [a, b]."""
    ab = b - a
    denom = np.dot(ab, ab)
    t = np.clip(np.dot(p - a, ab) / denom, 0.0, 1.0) if denom > 0 else 0.0
    return float(np.linalg.norm(p - (a + t * ab)))


def point_to_polyline_distance(p, poly) -> float:
    """Minimum distance from point p to any edge of poly."""
    return min(
        point_to_segment_distance(p, poly[i], poly[i + 1])
        for i in range(len(poly) - 1)
    )


def _interior_max_on_edge(a, b, Q) -> float:
    """
    Compute max_{t in [0,1]} g(t) where g(t) = min_i d(x(t), edge_i of Q)
    and x(t) = a + t*(b-a).

    Uses exact critical-point analysis via breakpoints (clamping transitions)
    and pairwise crossing roots (quadratic intersections of squared distances).
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    Q = np.asarray(Q, dtype=float)

    v = b - a
    n_edges = len(Q) - 1

    # Step 1: collect breakpoints where clamped-foot regime changes for each target edge
    breakpoints: set = set()
    for i in range(n_edges):
        c = Q[i]
        d = Q[i + 1]
        e = d - c
        denom = np.dot(v, e)
        if abs(denom) < 1e-12:
            continue
        t_lo = -np.dot(a - c, e) / denom
        t_hi = (np.dot(e, e) - np.dot(a - c, e)) / denom
        for t_val in (t_lo, t_hi):
            if 0.0 < t_val < 1.0:
                breakpoints.add(float(t_val))

    # Step 2: for each sub-interval between breakpoints, find crossing roots
    # where f_i(t) = f_j(t) (two target-edge squared-distances become equal)
    candidates_sorted = sorted({0.0, 1.0} | breakpoints)
    all_candidates: set = set(candidates_sorted)

    for idx in range(len(candidates_sorted) - 1):
        t_left = candidates_sorted[idx]
        t_right = candidates_sorted[idx + 1]
        t_mid = (t_left + t_right) * 0.5
        x_mid = a + t_mid * v

        # For each target edge, determine fixed clamped foot parameter at t_mid
        Av = float(np.dot(v, v))
        A_list: list = []
        B_list: list = []
        C_list: list = []
        for i in range(n_edges):
            c = Q[i]
            e = Q[i + 1] - c
            denom_e = float(np.dot(e, e))
            if denom_e > 0:
                s_i = float(np.clip(np.dot(x_mid - c, e) / denom_e, 0.0, 1.0))
            else:
                s_i = 0.0
            # f_i(t) = |x(t) - foot_i|^2  where foot_i = c + s_i*e (constant within sub-interval)
            w_i = a - (c + s_i * e)
            A_list.append(Av)
            B_list.append(2.0 * float(np.dot(w_i, v)))
            C_list.append(float(np.dot(w_i, w_i)))

        # Solve f_i(t) - f_j(t) = 0 for each pair (i, j)
        for i, j in itertools.combinations(range(n_edges), 2):
            A_diff = A_list[i] - A_list[j]
            B_diff = B_list[i] - B_list[j]
            C_diff = C_list[i] - C_list[j]
            if abs(A_diff) < 1e-14 and abs(B_diff) < 1e-14:
                continue
            roots = np.roots([A_diff, B_diff, C_diff])
            for r in roots:
                if np.isreal(r):
                    t_val = float(np.real(r))
                    if t_left < t_val < t_right:
                        all_candidates.add(t_val)

    # Step 3: evaluate g at all candidate t values and return the maximum
    best = 0.0
    for t_val in all_candidates:
        x = a + t_val * v
        g = point_to_polyline_distance(x, Q)
        if g > best:
            best = g
    return best


def polyline_hausdorff_distance(P, Q) -> float:
    """
    Symmetric arc-arc Hausdorff distance between two polylines.

    d_H(P, Q) = max(sup_{p in |P|} d(p, |Q|), sup_{q in |Q|} d(q, |P|))
             = max(d_PQ, d_QP)
    """
    P, Q = np.asarray(P, dtype=float), np.asarray(Q, dtype=float)
    d_PQ = max(_interior_max_on_edge(P[i], P[i + 1], Q) for i in range(len(P) - 1))
    d_QP = max(_interior_max_on_edge(Q[i], Q[i + 1], P) for i in range(len(Q) - 1))
    return max(d_PQ, d_QP)


def polylines_from_curve(curve, k) -> list:
    """Partition curve into non-overlapping k-edge polylines (stride = k)."""
    curve = np.asarray(curve, dtype=float)
    n = (len(curve) - 1) // k
    return [curve[j * k: j * k + k + 1] for j in range(n)]


def polyline_distance_matrix(polylines) -> np.ndarray:
    """Compute the symmetric pairwise Hausdorff distance matrix."""
    n = len(polylines)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = polyline_hausdorff_distance(polylines[i], polylines[j])
            D[i, j] = D[j, i] = d
    return D


def _build_vr_filtration_from_distances(
    n_vertices, D, max_radius=None, max_stages=None, max_dimension=2
) -> dict:
    """
    Build a Vietoris-Rips filtration directly from a precomputed distance matrix D.

    Parameters
    ----------
    n_vertices : int
        Number of vertices (polylines).
    D : np.ndarray, shape (n_vertices, n_vertices)
        Symmetric pairwise distance matrix.
    max_radius : float, optional
        Discard simplices born after this radius.
    max_stages : int, optional
        Quantise birth times to at most this many distinct values.
    max_dimension : int
        Maximum simplex dimension to include (default 2).

    Returns
    -------
    simplex_birth_time_map : dict
        {simplex (tuple[int, ...]): birth_radius (float)}
    """
    simplex_birth_time_map = {}
    max_dimension = int(max_dimension)
    if max_dimension < 0:
        raise ValueError("max_dimension must be >= 0")

    for i in range(n_vertices):
        simplex_birth_time_map[(i,)] = 0.0

    for simplex_size in range(2, max_dimension + 2):
        for simplex in itertools.combinations(range(n_vertices), simplex_size):
            birth = 0.0
            for i, j in itertools.combinations(simplex, 2):
                birth = max(birth, float(D[i, j]))

            if max_radius is not None and birth > float(max_radius):
                continue

            simplex_birth_time_map[tuple(simplex)] = birth

    if max_stages is not None:
        stage_count = int(max_stages)
        if stage_count <= 0:
            raise ValueError("max_stages must be >= 1")

        positive_births = sorted({
            float(b)
            for simplex, b in simplex_birth_time_map.items()
            if len(simplex) >= 2 and b > 0
        })

        if stage_count < len(positive_births) and positive_births:
            sample_idx = np.linspace(0, len(positive_births) - 1, stage_count, dtype=int)
            sampled_radii = [positive_births[i] for i in sample_idx]

            for simplex, birth in list(simplex_birth_time_map.items()):
                if len(simplex) == 1 or birth <= 0:
                    continue
                for sampled in sampled_radii:
                    if sampled >= birth:
                        simplex_birth_time_map[simplex] = float(sampled)
                        break
                else:
                    simplex_birth_time_map[simplex] = float(sampled_radii[-1])

    return simplex_birth_time_map
