import numpy as np

from core.crossings import find_crossings
from functions import (
    _build_event_order,
    _convert_A_poly_to_t_poly,
    _normalize_bracket_to_jones_in_A,
    generate_states,
    laurent_add,
    laurent_mul,
    laurent_pow,
    generate_unit_sphere_points
)

def find_open_crossings(curves, projection_vector=np.array([0, 0, 1])):
    from functions import project_to_2D
    crossings = []

    projected_curves = [project_to_2D(curve, projection_vector) for curve in curves]

    segments = []
    for ci, curve in enumerate(curves):
        curve_2d = projected_curves[ci]
        n_pts = len(curve)
        # 開曲線なので最後と最初を結ばない（ループさせない）
        for i in range(n_pts - 1):
            next_i = i + 1
            segments.append((ci, i, curve[i], curve[next_i], curve_2d[i], curve_2d[next_i]))

    n_segments = len(segments)
    if n_segments == 0:
        return crossings

    p1_2d = np.array([seg[4] for seg in segments])
    p2_2d = np.array([seg[5] for seg in segments])
    p1 = np.array([seg[2] for seg in segments])
    p2 = np.array([seg[3] for seg in segments])
    ci_arr = np.array([seg[0] for seg in segments])
    si_arr = np.array([seg[1] for seg in segments])

    dp = p2_2d - p1_2d
    dp_i = dp[:, np.newaxis, :]
    dp_j = dp[np.newaxis, :, :]
    p1_i = p1_2d[:, np.newaxis, :]
    p1_j = p1_2d[np.newaxis, :, :]
    
    detA = dp_j[:, :, 0] * dp_i[:, :, 1] - dp_i[:, :, 0] * dp_j[:, :, 1]
    valid_mask = np.abs(detA) > 1e-10

    i_idx, j_idx = np.triu_indices(n_segments, k=1)
    
    valid = valid_mask[i_idx, j_idx]
    i_valid = i_idx[valid]
    j_valid = j_idx[valid]

    ci1 = ci_arr[i_valid]
    ci2 = ci_arr[j_valid]
    si1 = si_arr[i_valid]
    si2 = si_arr[j_valid]
    
    diff = np.abs(si1 - si2)
    # 開曲線のため、最初と最後は隣接しない
    adj_mask = (ci1 == ci2) & (diff <= 1)
    
    non_adj = ~adj_mask
    i_final = i_valid[non_adj]
    j_final = j_valid[non_adj]
    
    if len(i_final) == 0:
        return crossings

    det_final = detA[i_final, j_final]
    
    bx = p1_j[0, j_final, 0] - p1_i[i_final, 0, 0]
    by = p1_j[0, j_final, 1] - p1_i[i_final, 0, 1]
    
    t = (by * dp_j[0, j_final, 0] - bx * dp_j[0, j_final, 1]) / det_final
    s = (dp_i[i_final, 0, 0] * by - dp_i[i_final, 0, 1] * bx) / det_final
    
    intersect_mask = (t >= 0) & (t <= 1) & (s >= 0) & (s <= 1)
    
    i_intersect = i_final[intersect_mask]
    j_intersect = j_final[intersect_mask]
    t_intersect = t[intersect_mask]
    s_intersect = s[intersect_mask]
    
    if len(i_intersect) > 0:
        p1_i3d = p1[i_intersect]
        dp_i3d = p2[i_intersect] - p1[i_intersect]
        p_z = p1_i3d + t_intersect[:, np.newaxis] * dp_i3d
        
        q1_i3d = p1[j_intersect]
        dq_i3d = p2[j_intersect] - p1[j_intersect]
        q_z = q1_i3d + s_intersect[:, np.newaxis] * dq_i3d
        
        pz_dot = np.dot(p_z, projection_vector)
        qz_dot = np.dot(q_z, projection_vector)
        p_over = pz_dot > qz_dot
        
        v_over = np.where(p_over[:, np.newaxis], dp_i3d, dq_i3d)
        v_under = np.where(p_over[:, np.newaxis], dq_i3d, dp_i3d)
        
        cross_prod = np.cross(v_over, v_under)
        dot_cross = np.dot(cross_prod, projection_vector)
        
        signs = np.where(dot_cross > 0, 1, -1)
        over_strs = np.where(p_over, "p_over", "q_over")
        
        for k in range(len(i_intersect)):
            crossings.append({
                "segments": (int(i_intersect[k]), int(j_intersect[k])),
                "curves": (int(ci_arr[i_intersect[k]]), int(ci_arr[j_intersect[k]])),
                "t": float(t_intersect[k]),
                "s": float(s_intersect[k]),
                "over": str(over_strs[k]),
                "sign": int(signs[k])
            })
            
    return crossings


def count_open_curve_state_cycles_by_orbits(crossings, state, n_curves=1):
    """
    開曲線向けのサイクル数（コンポーネント数）カウント。
    曲線の端点同士を結ばず、開いたパスも1つのコンポーネントとしてカウントする。
    """
    n_crossings = len(crossings)
    if n_crossings == 0:
        return n_curves

    ordered_events = _build_event_order(crossings)
    missing_curves = n_curves - len(ordered_events)

    halfedge_id = {}
    next_id = 0
    for curve_events in ordered_events:
        for event in curve_events:
            crossing_index, branch_index = event
            halfedge_id[(crossing_index, branch_index, "in")] = next_id
            next_id += 1
            halfedge_id[(crossing_index, branch_index, "out")] = next_id
            next_id += 1

    n_halfedges = next_id
    arc_map = {}
    
    for curve_events in ordered_events:
        n_events = len(curve_events)
        # 閉曲線の場合は (i + 1) % n_events としていたが
        # 開曲線の場合は最後の out と最初の in を繋がない
        for i in range(n_events - 1):
            curr_c, curr_b = curve_events[i]
            next_c, next_b = curve_events[i + 1]
            out_id = halfedge_id[(curr_c, curr_b, "out")]
            in_next_id = halfedge_id[(next_c, next_b, "in")]
            arc_map[out_id] = in_next_id
            arc_map[in_next_id] = out_id
            
    smooth_map = {}
    for crossing_index, label in enumerate(state):
        in0 = halfedge_id[(crossing_index, 0, "in")]
        out0 = halfedge_id[(crossing_index, 0, "out")]
        in1 = halfedge_id[(crossing_index, 1, "in")]
        out1 = halfedge_id[(crossing_index, 1, "out")]

        pattern_1 = ((in0, out1), (out0, in1))
        pattern_2 = ((in0, in1), (out0, out1))

        crossing_sign_value = crossings[crossing_index]["sign"]
        if crossing_sign_value > 0:
            pairs = pattern_1 if label == +1 else pattern_2
        else:
            pairs = pattern_2 if label == +1 else pattern_1

        for left, right in pairs:
            smooth_map[left] = right
            smooth_map[right] = left

    # ArcとSmoothを辿る
    # perm_map は完全な対応とは限らない (開端点があるため)
    adjacency = {}
    for i in range(n_halfedges):
        adjacency[i] = []
        if i in arc_map:
            adjacency[i].append(arc_map[i])
        if i in smooth_map:
            adjacency[i].append(smooth_map[i])
            
    visited = set()
    component_count = 0
    
    for start in range(n_halfedges):
        if start in visited:
            continue
        
        # 幅優先/深さ優先探索で連結成分を見つける
        queue = [start]
        visited.add(start)
        
        while queue:
            curr = queue.pop(0)
            for neighbor in adjacency[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    
        component_count += 1

    return component_count + missing_curves


def sigma(state):
    return sum(state)


def open_curve_kauffman_bracket(crossings, n_curves=1):
    d_poly = {2: -1, -2: -1}  # -A^2 - A^-2

    n_crossings = len(crossings)
    if n_crossings == 0:
        return laurent_pow(d_poly, n_curves - 1)

    states = generate_states(n_crossings)
    bracket = {}

    for state in states:
        sigma_s = sigma(state)
        # 開曲線用のコンポーネント数カウント
        component_count = count_open_curve_state_cycles_by_orbits(crossings, state, n_curves)

        state_poly = {sigma_s: 1}
        # -A^2 - A^-2 で正規化するかどうかは既存実装に合わせる
        state_poly = laurent_mul(state_poly, laurent_pow(d_poly, component_count - 1))
        bracket = laurent_add(bracket, state_poly)

    return bracket


def open_curve_jones_polynomial(curves, projection_vector=np.array([0, 0, 1])):
    """
    開曲線向けの Jones 多項式を t 変数の係数辞書で返す。
    curves: [np.array([[x,y,z], ...]), ...] のリスト
    """
    crossings = find_open_crossings(curves, projection_vector=projection_vector)

    bracket_A = open_curve_kauffman_bracket(crossings, n_curves=len(curves))
    normalized_A = _normalize_bracket_to_jones_in_A(bracket_A, crossings)
    return _convert_A_poly_to_t_poly(normalized_A)

def open_curve_PJP(curves, Number_of_projections=1000, RANDOM_SEED=42):
    mean_jp = {}
    sphere_points = generate_unit_sphere_points(Number_of_projections, RANDOM_SEED)
    for i, projection_vector in enumerate(sphere_points):
        # print(f"Projection {i+1}/{Number_of_projections}")
        jp = open_curve_jones_polynomial(curves, projection_vector=projection_vector)
        mean_jp = laurent_add(mean_jp, jp)
    mean_jp = {k: v / Number_of_projections for k, v in mean_jp.items()}
    return mean_jp

def open_curve_crossing_info(curves, Number_of_projections=1000, RANDOM_SEED=42):
    crossing_info = {}
    crossing_nums = []
    count = 0
    sphere_points = generate_unit_sphere_points(Number_of_projections, RANDOM_SEED)
    for projection_vector in sphere_points:
        crossings = find_open_crossings(curves, projection_vector=projection_vector)
        num_crossings = len(crossings)
        if num_crossings == 0:
            count += 1
        crossing_nums.append(num_crossings)
        crossing_info[tuple(projection_vector)] = crossings
    # print(f"Average number of crossings: {np.mean(crossing_nums)}")
    max_crossings = np.max(crossing_nums)
    if max_crossings > 0:
        print(f"Max number of crossings: {max_crossings}")
    # print(f"Number of projections with no crossings: {count}")
    return crossing_info, crossing_nums

def knotoid_linking_num(curves, projection_vector=np.array([0, 0, 1])):
    crossings = find_open_crossings(curves, projection_vector=projection_vector)
    linking_num = 0
    for crossing in crossings:
        if crossing["sign"] > 0:
            linking_num += 1
        else:
            linking_num -= 1
    linking_num /= 2

    return linking_num

def open_curve_Linking_num(curves, Number_of_projections=1000, RANDOM_SEED=42):
    mean_Linking_num = 0
    sphere_points = generate_unit_sphere_points(Number_of_projections, RANDOM_SEED)
    for i, projection_vector in enumerate(sphere_points):
        # print(f"Projection {i+1}/{Number_of_projections}")
        Linking_num = knotoid_linking_num(curves, projection_vector=projection_vector)
        mean_Linking_num += Linking_num
    mean_Linking_num /= Number_of_projections
    return mean_Linking_num