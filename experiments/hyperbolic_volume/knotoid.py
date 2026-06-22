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

if __name__ == "__main__":
    import numpy as np


    def _projection_basis(projection_vector):
        n = np.asarray(projection_vector, dtype=float)
        n = n / np.linalg.norm(n)

        tmp = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(tmp, n)) > 0.9:
            tmp = np.array([0.0, 1.0, 0.0])

        e1 = np.cross(tmp, n)
        e1 = e1 / np.linalg.norm(e1)
        e2 = np.cross(n, e1)

        return n, e1, e2


    def _project_points(points, e1, e2):
        points = np.asarray(points, dtype=float)
        return np.column_stack((points @ e1, points @ e2))


    def knotoid_to_snappy_pd(curve, projection_vector=np.array([0, 0, 1]), eps=1e-10):
        """
        開曲線 knotoid を仮想閉包し、通常交点だけから SnapPy 用 PD code を作る。

        curve:
            shape (N, 3) の開曲線。
            curve[-1] == curve[0] でない想定。

        Returns:
            list[tuple[int, int, int, int]]
            SnapPy の snappy.Link(pd) に渡す PD code。

        注意:
            閉じ線 curve[-1] -> curve[0] が作る交点は virtual crossing として無視する。
        """

        curve = np.asarray(curve, dtype=float)

        if len(curve) < 2:
            return []

        proj_vec, e1, e2 = _projection_basis(projection_vector)

        # original segments: curve[i] -> curve[i + 1]
        # closure segment: curve[-1] -> curve[0]
        seg_starts = []
        seg_ends = []
        seg_indices = []
        is_closure = []

        for i in range(len(curve) - 1):
            seg_starts.append(curve[i])
            seg_ends.append(curve[i + 1])
            seg_indices.append(i)
            is_closure.append(False)

        closure_index = len(curve) - 1
        seg_starts.append(curve[-1])
        seg_ends.append(curve[0])
        seg_indices.append(closure_index)
        is_closure.append(True)

        seg_starts = np.asarray(seg_starts)
        seg_ends = np.asarray(seg_ends)
        is_closure = np.asarray(is_closure, dtype=bool)

        p1_2d = _project_points(seg_starts, e1, e2)
        p2_2d = _project_points(seg_ends, e1, e2)

        dp_2d = p2_2d - p1_2d
        n_segments = len(seg_starts)

        classical_crossings = []
        crossing_events = []
        events = []

        for i in range(n_segments):
            for j in range(i + 1, n_segments):
                si = seg_indices[i]
                sj = seg_indices[j]

                # 元の開曲線上で隣り合う線分は、共有端点なので除外
                if not is_closure[i] and not is_closure[j]:
                    if abs(si - sj) <= 1:
                        continue

                # 閉じ線と、端点を共有する最初/最後の線分は除外
                if is_closure[i] != is_closure[j]:
                    original_si = sj if is_closure[i] else si
                    if original_si == 0 or original_si == len(curve) - 2:
                        continue

                a = dp_2d[i]
                b = dp_2d[j]
                c = p1_2d[j] - p1_2d[i]

                det = b[0] * a[1] - a[0] * b[1]
                if abs(det) <= eps:
                    continue

                t = (c[1] * b[0] - c[0] * b[1]) / det
                s = (a[0] * c[1] - a[1] * c[0]) / det

                if not (eps < t < 1.0 - eps and eps < s < 1.0 - eps):
                    continue

                # 閉じ線に関わる交点は virtual crossing として PD には入れない
                if is_closure[i] or is_closure[j]:
                    continue

                p3 = seg_starts[i] + t * (seg_ends[i] - seg_starts[i])
                q3 = seg_starts[j] + s * (seg_ends[j] - seg_starts[j])

                p_depth = np.dot(p3, proj_vec)
                q_depth = np.dot(q3, proj_vec)

                p_is_over = p_depth > q_depth

                event_i = {
                    "segment": si,
                    "param": float(t),
                    "is_over": bool(p_is_over),
                }

                event_j = {
                    "segment": sj,
                    "param": float(s),
                    "is_over": bool(not p_is_over),
                }

                events.append(event_i)
                events.append(event_j)

                classical_crossings.append((i, j))
                crossing_events.append((event_i, event_j))

        if not crossing_events:
            return []

        # 開曲線 + 仮想閉じ線を一周する順番で半弧ラベルを付ける。
        # virtual crossing はラベル付けでは無視する。
        events.sort(key=lambda ev: (ev["segment"], ev["param"]))

        arc_label = 1
        n_events = len(events)

        for k, ev in enumerate(events):
            next_ev = events[(k + 1) % n_events]

            ev["out"] = arc_label
            next_ev["in"] = arc_label

            arc_label += 1

        pd = []

        for (seg_i, seg_j), (event_i, event_j) in zip(classical_crossings, crossing_events):
            dir_i = seg_ends[seg_i] - seg_starts[seg_i]
            dir_j = seg_ends[seg_j] - seg_starts[seg_j]

            dir_i_2d = np.array([np.dot(dir_i, e1), np.dot(dir_i, e2)])
            dir_j_2d = np.array([np.dot(dir_j, e1), np.dot(dir_j, e2)])

            rays = [
                (event_i["in"],  event_i["is_over"], -dir_i_2d),
                (event_i["out"], event_i["is_over"],  dir_i_2d),
                (event_j["in"],  event_j["is_over"], -dir_j_2d),
                (event_j["out"], event_j["is_over"],  dir_j_2d),
            ]

            rays.sort(key=lambda r: np.arctan2(r[2][1], r[2][0]))

            # SnapPy/Spherogram は (under, over, under, over)
            start = next(k for k, r in enumerate(rays) if not r[1])
            rays = rays[start:] + rays[:start]

            pd.append(tuple(r[0] for r in rays))

        return pd
    
    # 動作を確認するために、単純な knotoid を生成したい
    