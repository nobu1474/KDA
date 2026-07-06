import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import snappy
import tkinter as tk
from experiments.hyperbolic_volume.torus_hopf_volume import build_components, detect_crossings, build_occurrences, crossing_label_table, pd_candidates
from experiments.hyperbolic_volume.knot_to_PD import crossings_to_pd
from data.generate_point_cloud import generate_unit_nm_torus_points
from functions import find_crossings
from visualization.point_cloud import plot_3d_point_cloud

Point2 = Tuple[float, float]
Point3 = Tuple[float, float, float]
Point4 = Tuple[float, float, float, float]

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

def main() -> None:
    components = build_components(EXAMPLE_TORUS_PATHS)
    crossings = detect_crossings(components)
    # print(f"PD code: {crossings}")

    n=2
    m=3
    curve = generate_unit_nm_torus_points(500, evenly_spaced=False, n=n, m=m)
    open_curve = curve[0][0:250]  # 途中の部分を切り出して開曲線にする
    plot_3d_point_cloud(open_curve, title="Open Torus Knot Curve")
    crossings = find_crossings(curve) 

    pd_code = crossings_to_pd(curve, crossings)
    # print(f"PD code: {pd_code}")

    L = snappy.Link(pd_code)

    L.view()
    # tk.mainloop() # ウィンドウが一瞬で閉じないように画面を維持する

    M = L.exterior()

    print(M.volume())



if __name__ == "__main__":
    main()
