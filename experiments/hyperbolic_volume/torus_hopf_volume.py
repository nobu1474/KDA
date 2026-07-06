#!/usr/bin/env python3
"""
Prototype: torus diagram -> Hopf-augmented link -> PD-like code -> SnapPy volume.

This is meant as a research scaffold for spherical knotoids under the
reflected doubling map.  The input is a closed curve on the torus, written in
unwrapped coordinates (u, v), where (u, v) and (u + m, v + n) represent the
same point of T^2.  The script embeds T^2 x I into S^3, adds the two Hopf
core components z1 = 0 and z2 = 0, projects to the plane, detects crossings,
and produces oriented crossing data.

If SnapPy/Spherogram is installed, the script also tries several common PD
tuple conventions and reports candidate volumes.  The reflected-doubling
knotoid volume is half the volume of the doubled complement.

Install SnapPy locally if needed:

    python3 -m pip install snappy

Run:

    python3 torus_hopf_volume.py

Replace EXAMPLE_TORUS_PATHS with the torus curve obtained from your reflected
doubling construction.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


Point2 = Tuple[float, float]
Point3 = Tuple[float, float, float]
Point4 = Tuple[float, float, float, float]


# ---------------------------------------------------------------------------
# Example input
# ---------------------------------------------------------------------------

# A toy curve on the torus in unwrapped coordinates.  This is not meant to be
# a verified knotoid table example; it is just a nontrivial curve that exercises
# the pipeline.  Replace this by the reflected-doubling image of your knotoid.
#
# Important:
# - Coordinates are modulo Z^2.
# - The path should close modulo Z^2.
# - Use unwrapped coordinates when the curve crosses a fundamental-domain edge.
EXAMPLE_TORUS_PATHS: List[List[Point2]] = [
    [
        (0.07, 0.10),
        (0.34, 0.84),
        (0.68, 0.18),
        (1.12, 0.72),
        (1.45, 1.10),
        (0.07, 0.10),
    ]
]


# ---------------------------------------------------------------------------
# Geometry: T^2 x I inside S^3, then stereographic projection to R^3
# ---------------------------------------------------------------------------


def s3_torus_point(u: float, v: float, rho: float = 0.0) -> Point4:
    """Point in S^3 from thickened torus coordinates.

    S^3 is written as {(z1, z2) in C^2 : |z1|^2 + |z2|^2 = 1}.
    The Clifford torus is |z1|^2 = |z2|^2 = 1/2.

    rho is a small normal parameter.  Use rho = 0 for the torus itself.
    """

    if not (-0.49 < rho < 0.49):
        raise ValueError("rho must lie in (-0.49, 0.49)")
    theta = 2.0 * math.pi * u
    phi = 2.0 * math.pi * v
    r1 = math.sqrt(0.5 + rho)
    r2 = math.sqrt(0.5 - rho)
    return (
        r1 * math.cos(theta),
        r1 * math.sin(theta),
        r2 * math.cos(phi),
        r2 * math.sin(phi),
    )


def hopf_component_1(samples: int = 240) -> List[Point4]:
    """Hopf component z1 = 0, z2 = exp(i t)."""

    return [
        (0.0, 0.0, math.cos(2.0 * math.pi * i / samples), math.sin(2.0 * math.pi * i / samples))
        for i in range(samples + 1)
    ]


def hopf_component_2(samples: int = 240) -> List[Point4]:
    """Hopf component z2 = 0, z1 = exp(i t)."""

    return [
        (math.cos(2.0 * math.pi * i / samples), math.sin(2.0 * math.pi * i / samples), 0.0, 0.0)
        for i in range(samples + 1)
    ]


def stereographic_projection(q: Point4) -> Point3:
    """Generic stereographic projection S^3 -> R^3.

    We first rotate coordinates so that neither Hopf component hits the
    projection point.  In old coordinates q = (X, Y, Z, W), take

        w = (X + Z) / sqrt(2)

    as the north-pole coordinate and project from w = 1.
    """

    x, y, z, w_old = q
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    a = (x - z) * inv_sqrt2
    b = y
    c = w_old
    w = (x + z) * inv_sqrt2
    den = 1.0 - w
    if abs(den) < 1e-8:
        raise ValueError("projection point too close to a curve point")
    return (a / den, b / den, c / den)


def sample_torus_path(path: Sequence[Point2], per_segment: int = 24, rho: float = 0.0) -> List[Point3]:
    """Sample an unwrapped torus path and project it to R^3."""

    pts: List[Point3] = []
    for a, b in zip(path, path[1:]):
        for k in range(per_segment):
            t = k / per_segment
            u = (1.0 - t) * a[0] + t * b[0]
            v = (1.0 - t) * a[1] + t * b[1]
            pts.append(stereographic_projection(s3_torus_point(u, v, rho=rho)))
    pts.append(stereographic_projection(s3_torus_point(path[-1][0], path[-1][1], rho=rho)))
    return pts


def sample_s3_path(path: Sequence[Point4]) -> List[Point3]:
    return [stereographic_projection(p) for p in path]


# ---------------------------------------------------------------------------
# Projection crossing detection
# ---------------------------------------------------------------------------


@dataclass
class Crossing:
    index: int
    comp_a: int
    seg_a: int
    ta: float
    comp_b: int
    seg_b: int
    tb: float
    over: str  # "a" or "b"
    # sign: int


@dataclass
class Occurrence:
    crossing: int
    comp: int
    seg: int
    t: float
    is_over: bool
    in_label: Optional[int] = None
    out_label: Optional[int] = None


def orient2(a: Point2, b: Point2, c: Point2) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segment_intersection(
    p: Point3, p2: Point3, q: Point3, q2: Point3, eps: float = 1e-9
) -> Optional[Tuple[float, float]]:
    """Return segment parameters (t, u) for a proper xy-intersection."""

    x1, y1 = p[0], p[1]
    x2, y2 = p2[0], p2[1]
    x3, y3 = q[0], q[1]
    x4, y4 = q2[0], q2[1]
    dx1 = x2 - x1
    dy1 = y2 - y1
    dx2 = x4 - x3
    dy2 = y4 - y3
    den = dx1 * dy2 - dy1 * dx2
    if abs(den) < eps:
        return None
    t = ((x3 - x1) * dy2 - (y3 - y1) * dx2) / den
    u = ((x3 - x1) * dy1 - (y3 - y1) * dx1) / den
    if eps < t < 1.0 - eps and eps < u < 1.0 - eps:
        return t, u
    return None


def height_at(p: Point3, q: Point3, t: float) -> float:
    return (1.0 - t) * p[2] + t * q[2]


def detect_crossings(components: Sequence[Sequence[Point3]]) -> List[Crossing]:
    crossings: List[Crossing] = []
    for ca, cb in itertools.combinations_with_replacement(range(len(components)), 2):
        a_pts = components[ca]
        b_pts = components[cb]
        for ia in range(len(a_pts) - 1):
            jb_start = ia + 2 if ca == cb else 0
            for ib in range(jb_start, len(b_pts) - 1):
                if ca == cb:
                    # Adjacent segments share an endpoint; skip them.  Also skip
                    # first-last adjacency for closed polylines.
                    if abs(ia - ib) <= 1:
                        continue
                    if ia == 0 and ib == len(b_pts) - 2:
                        continue
                hit = segment_intersection(a_pts[ia], a_pts[ia + 1], b_pts[ib], b_pts[ib + 1])
                if hit is None:
                    continue
                ta, tb = hit
                za = height_at(a_pts[ia], a_pts[ia + 1], ta)
                zb = height_at(b_pts[ib], b_pts[ib + 1], tb)
                if abs(za - zb) < 1e-7:
                    # A numerically nongeneric projection.  Perturb the path or
                    # change projection if this appears.
                    continue
                crossings.append(
                    Crossing(
                        index=len(crossings) + 1,
                        comp_a=ca,
                        seg_a=ia,
                        ta=ta,
                        comp_b=cb,
                        seg_b=ib,
                        tb=tb,
                        over="a" if za > zb else "b",
                    )
                )
    return crossings


def build_occurrences(components: Sequence[Sequence[Point3]], crossings: Sequence[Crossing]) -> Dict[int, List[Occurrence]]:
    occs: Dict[int, List[Occurrence]] = {i: [] for i in range(len(components))}
    for cr in crossings:
        occs[cr.comp_a].append(
            Occurrence(cr.index, cr.comp_a, cr.seg_a, cr.ta, is_over=(cr.over == "a"))
        )
        occs[cr.comp_b].append(
            Occurrence(cr.index, cr.comp_b, cr.seg_b, cr.tb, is_over=(cr.over == "b"))
        )

    next_label = 1
    for comp, items in occs.items():
        items.sort(key=lambda o: (o.seg, o.t))
        n = len(items)
        if n == 0:
            continue
        labels = list(range(next_label, next_label + n))
        next_label += n
        for i, occ in enumerate(items):
            occ.in_label = labels[i - 1]
            occ.out_label = labels[i]
    return occs


def crossing_label_table(occs: Dict[int, List[Occurrence]]) -> Dict[int, Dict[str, Tuple[int, int]]]:
    table: Dict[int, Dict[str, Tuple[int, int]]] = {}
    for items in occs.values():
        for occ in items:
            key = "over" if occ.is_over else "under"
            table.setdefault(occ.crossing, {})[key] = (int(occ.in_label), int(occ.out_label))
    return table


def pd_candidates(label_table: Dict[int, Dict[str, Tuple[int, int]]]) -> Dict[str, List[Tuple[int, int, int, int]]]:
    """Common PD tuple conventions to try with Spherogram/SnapPy.

    PD conventions differ.  We report several candidates.  Mirror images have
    the same hyperbolic volume, so more than one candidate may be useful.
    """

    rows = []
    for i in sorted(label_table):
        under_in, under_out = label_table[i]["under"]
        over_in, over_out = label_table[i]["over"]
        rows.append((under_in, under_out, over_in, over_out))

    return {
        "Uin_Oin_Uout_Oout": [(ui, oi, uo, oo) for ui, uo, oi, oo in rows],
        "Uin_Oout_Uout_Oin": [(ui, oo, uo, oi) for ui, uo, oi, oo in rows],
    }


def try_snappy(pd_by_name: Dict[str, List[Tuple[int, int, int, int]]]) -> None:
    try:
        import snappy  # type: ignore
    except Exception as e:
        print("\nSnapPy is not installed, so volume computation was skipped.")
        print(f"Import error: {e}")
        return

    print("\nSnapPy candidates:")
    for name, pd in pd_by_name.items():
        try:
            link = snappy.Link(pd)
            manifold = link.exterior()
            vol = manifold.volume()
            print(f"- {name}: volume={vol:.12f}, reflected_doubling_volume={vol / 2.0:.12f}")
            try:
                print(f"  solution_type={manifold.solution_type()}")
            except Exception:
                pass
        except Exception as e:
            print(f"- {name}: rejected by SnapPy/Spherogram ({e})")


def build_components(
    torus_paths: Sequence[Sequence[Point2]],
    torus_samples_per_segment: int = 32,
    hopf_samples: int = 240,
    rho: float = 0.0,
) -> List[List[Point3]]:
    components: List[List[Point3]] = []
    for path in torus_paths:
        components.append(sample_torus_path(path, per_segment=torus_samples_per_segment, rho=rho))
    components.append(sample_s3_path(hopf_component_1(samples=hopf_samples)))
    components.append(sample_s3_path(hopf_component_2(samples=hopf_samples)))
    return components


def main() -> None:
    components = build_components(EXAMPLE_TORUS_PATHS)
    crossings = detect_crossings(components)
    occs = build_occurrences(components, crossings)
    label_table = crossing_label_table(occs)
    pd_by_name = pd_candidates(label_table)

    print("Components:")
    for i, comp in enumerate(components):
        kind = "torus knot component" if i < len(EXAMPLE_TORUS_PATHS) else "Hopf component"
        print(f"- component {i}: {kind}, sampled vertices={len(comp)}")

    print(f"\nDetected crossings: {len(crossings)}")
    for cr in crossings:
        print(
            f"X{cr.index}: "
            f"comp {cr.comp_a} seg {cr.seg_a} t={cr.ta:.3f} "
            f"with comp {cr.comp_b} seg {cr.seg_b} t={cr.tb:.3f}; "
            f"over={'first' if cr.over == 'a' else 'second'}"
        )

    print("\nOriented crossing labels:")
    print("# crossing: under(in,out), over(in,out)")
    for i in sorted(label_table):
        print(f"X{i}: under={label_table[i]['under']}, over={label_table[i]['over']}")

    print("\nPD candidates:")
    for name, pd in pd_by_name.items():
        print(f"{name} = {pd}")

    try_snappy(pd_by_name)


if __name__ == "__main__":
    main()
