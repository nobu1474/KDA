# 三次元曲線からPD(Planar Diagram)を作りたい
# 最終的にはknotoid linkoid に対するPDを作ることを目標にする
# knotoid/linkoid は射影方向によって異なるので少し大変（平均をとる）なので
# まずは結び目に対して作る

import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.generate_point_cloud import generate_unit_nm_torus_points
from model.knot import Knot
from functions import find_crossings
from visualization.point_cloud import plot_3d_point_cloud

def crossings_to_pd(curves, crossings, projection_vector=np.array([0, 0, 1])):
    """
    find_crossings(curves, projection_vector) の結果から
    SnapPy の Link(PD_code) に渡す PD code を作る。

    SnapPy/Spherogram の crossing tuple は、
        (under, over, under, over)
    という位置関係を持つ必要がある。

    Returns
    -------
    list[tuple[int, int, int, int]]
    """

    if not crossings:
        return []

    projection_vector = np.asarray(projection_vector, dtype=float)
    projection_vector = projection_vector / np.linalg.norm(projection_vector)

    # 射影平面上の右手系基底を作る
    tmp = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(tmp, projection_vector)) > 0.9:
        tmp = np.array([0.0, 1.0, 0.0])

    e1 = np.cross(tmp, projection_vector)
    e1 = e1 / np.linalg.norm(e1)
    e2 = np.cross(projection_vector, e1)

    # global segment index -> (curve index, segment index)
    segment_to_curve = []
    for ci, curve in enumerate(curves):
        for si in range(len(curve)):
            segment_to_curve.append((ci, si))

    # 各曲線上の交点イベント
    events_by_curve = [[] for _ in curves]
    crossing_events = []

    for crossing_index, cr in enumerate(crossings):
        seg_p, seg_q = cr["segments"]

        ci_p, si_p = segment_to_curve[seg_p]
        ci_q, si_q = segment_to_curve[seg_q]

        p_is_over = cr["over"] == "p_over"

        event_p = {
            "crossing": crossing_index,
            "is_over": p_is_over,
            "segment": si_p,
            "param": cr["t"],
        }

        event_q = {
            "crossing": crossing_index,
            "is_over": not p_is_over,
            "segment": si_q,
            "param": cr["s"],
        }

        events_by_curve[ci_p].append(event_p)
        events_by_curve[ci_q].append(event_q)
        crossing_events.append((event_p, event_q))

    # 曲線の向きに沿って半弧ラベルを付ける
    label = 1

    for events in events_by_curve:
        if not events:
            continue

        events.sort(key=lambda ev: (ev["segment"], ev["param"]))

        n = len(events)
        for i, ev in enumerate(events):
            next_ev = events[(i + 1) % n]

            ev["out"] = label
            next_ev["in"] = label

            label += 1

    pd = []

    for cr, (event_p, event_q) in zip(crossings, crossing_events):
        seg_p, seg_q = cr["segments"]

        ci_p, si_p = segment_to_curve[seg_p]
        ci_q, si_q = segment_to_curve[seg_q]

        curve_p = curves[ci_p]
        curve_q = curves[ci_q]

        n_p = len(curve_p)
        n_q = len(curve_q)

        dir_p = np.asarray(curve_p[(si_p + 1) % n_p]) - np.asarray(curve_p[si_p])
        dir_q = np.asarray(curve_q[(si_q + 1) % n_q]) - np.asarray(curve_q[si_q])

        dir_p_2d = np.array([np.dot(dir_p, e1), np.dot(dir_p, e2)])
        dir_q_2d = np.array([np.dot(dir_q, e1), np.dot(dir_q, e2)])

        rays = [
            {
                "label": event_p["in"],
                "kind": "over" if event_p["is_over"] else "under",
                "direction": -dir_p_2d,
            },
            {
                "label": event_p["out"],
                "kind": "over" if event_p["is_over"] else "under",
                "direction": dir_p_2d,
            },
            {
                "label": event_q["in"],
                "kind": "over" if event_q["is_over"] else "under",
                "direction": -dir_q_2d,
            },
            {
                "label": event_q["out"],
                "kind": "over" if event_q["is_over"] else "under",
                "direction": dir_q_2d,
            },
        ]

        # 交点の周りの反時計回り順
        rays.sort(key=lambda r: np.arctan2(r["direction"][1], r["direction"][0]))

        # SnapPy 用に、0番目が under になるように回転する。
        # すると 0,2 が under、1,3 が over になる。
        under_start = next(i for i, r in enumerate(rays) if r["kind"] == "under")
        rays = rays[under_start:] + rays[:under_start]

        pd.append(tuple(r["label"] for r in rays))

    return pd

if __name__ == "__main__":
    n=3
    m=9
    curve = generate_unit_nm_torus_points(500, evenly_spaced=False, n=n, m=m)
    # print(curve)
    # plot_3d_point_cloud(curve, title="Torus Knot Curve")
    crossings = find_crossings(curve) # 始点と終点のごたつきでおかしくなるので、最後の点を除外する
    # print(f"Crossings: {crossings}")
    # print(f"Number of crossings: {len(crossings)}")


    pd_code = crossings_to_pd(curve, crossings) 
    print(f"PD code: {pd_code}")


    import snappy
    import tkinter as tk  # ウィンドウを維持するためにインポート

    L = snappy.Link(pd_code)

    L.view()
    tk.mainloop() # ウィンドウが一瞬で閉じないように画面を維持する

    M = L.exterior()

    print(M.volume())

