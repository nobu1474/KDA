"""Polyline-based Vietoris-Rips filtration using exact arc-arc Hausdorff distance."""

import itertools

import numpy as np

_EPS = 1e-12


def point_to_segment_distance(p, a, b) -> float:
    """Exact distance from point p to segment [a, b]."""
    p, a, b = np.asarray(p, dtype=float), np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    ab = b - a
    denom = np.dot(ab, ab)
    t = np.clip(np.dot(p - a, ab) / denom, 0.0, 1.0) if denom > 0 else 0.0
    return float(np.linalg.norm(p - (a + t * ab)))


def point_to_polyline_distance(p, poly) -> float:
    """Minimum distance from point p to any edge of poly."""
    poly = np.asarray(poly, dtype=float)
    if len(poly) < 2:
        raise ValueError("polyline must contain at least two points")
    return min(
        point_to_segment_distance(p, poly[i], poly[i + 1])
        for i in range(len(poly) - 1)
    )


def _segment_distance_squared_coefficients(a, v, c, d, t_mid):
    """Return A, B, C for squared distance from a+t*v to segment [c, d]."""
    e = d - c
    denom_e = float(np.dot(e, e))

    if denom_e <= _EPS:
        r0 = a - c
        r1 = v
    else:
        s_mid = float(np.dot(a + t_mid * v - c, e) / denom_e)
        if s_mid <= 0.0:
            r0 = a - c
            r1 = v
        elif s_mid >= 1.0:
            r0 = a - d
            r1 = v
        else:
            u = a - c
            r0 = u - (float(np.dot(u, e)) / denom_e) * e
            r1 = v - (float(np.dot(v, e)) / denom_e) * e

    return (
        float(np.dot(r1, r1)),
        2.0 * float(np.dot(r0, r1)),
        float(np.dot(r0, r0)),
    )


def _real_roots_in_open_interval(A, B, C, t_left, t_right):
    """Solve A*t^2 + B*t + C = 0 and keep real roots inside an interval."""
    if abs(A) <= 1e-14:
        if abs(B) <= 1e-14:
            return []
        roots = [-C / B]
    else:
        discriminant = B * B - 4.0 * A * C
        if discriminant < -1e-14:
            return []
        if discriminant < 0.0:
            discriminant = 0.0
        sqrt_disc = float(np.sqrt(discriminant))
        roots = [(-B - sqrt_disc) / (2.0 * A), (-B + sqrt_disc) / (2.0 * A)]

    return [
        float(root)
        for root in roots
        if t_left < float(root) < t_right
    ]


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
        if abs(denom) < _EPS:
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

        A_list: list = []
        B_list: list = []
        C_list: list = []
        for i in range(n_edges):
            c = Q[i]
            d = Q[i + 1]
            A, B, C = _segment_distance_squared_coefficients(a, v, c, d, t_mid)
            A_list.append(A)
            B_list.append(B)
            C_list.append(C)

        # Solve f_i(t) - f_j(t) = 0 for each pair (i, j)
        for i, j in itertools.combinations(range(n_edges), 2):
            A_diff = A_list[i] - A_list[j]
            B_diff = B_list[i] - B_list[j]
            C_diff = C_list[i] - C_list[j]
            for t_val in _real_roots_in_open_interval(A_diff, B_diff, C_diff, t_left, t_right):
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
    if len(P) < 2 or len(Q) < 2:
        raise ValueError("polylines must contain at least two points")
    d_PQ = max(_interior_max_on_edge(P[i], P[i + 1], Q) for i in range(len(P) - 1))
    d_QP = max(_interior_max_on_edge(Q[i], Q[i + 1], P) for i in range(len(Q) - 1))
    return max(d_PQ, d_QP)


def polylines_from_curve(curve, k) -> list:
    """Partition curve into consecutive polylines without dropping tail edges."""
    curve = np.asarray(curve, dtype=float)
    k = int(k)
    if k <= 0:
        raise ValueError("k must be >= 1")
    if len(curve) < 2:
        raise ValueError("curve must contain at least two points")
    return [
        curve[start: min(start + k, len(curve) - 1) + 1]
        for start in range(0, len(curve) - 1, k)
    ]


def polyline_distance_matrix(polylines) -> np.ndarray:
    """Compute the symmetric pairwise Hausdorff distance matrix."""
    n = len(polylines)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = polyline_hausdorff_distance(polylines[i], polylines[j])
            D[i, j] = D[j, i] = d
    return D


def build_vr_filtration_from_distances(
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
            if stage_count == 1:
                sampled_radii = [positive_births[-1]]
            else:
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
