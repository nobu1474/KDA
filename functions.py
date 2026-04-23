"""
3D曲線
↓
2Dに射影
↓
線分同士の交差判定
↓
交点ごとに
  ・どの2線分か
  ・パラメータ位置
  ・over / under
  ・符号 (+1 / -1)
を計算
"""

# 交点の情報を保持するクラス
# xy平面に射影して交点を検出するための関数群
# 他の方向にも対応させるためには、射影面を指定できるようにする必要があるかも

# 1. 2D交差判定

import numpy as np
from math import gcd
import plotly.graph_objects as go
from pathlib import Path

def orient(a, b, c):
    """
    符号付き面積（向き判定）
    入力は2次元数ベクトル(座標)
    aを基準点として、bとcの位置関係を判定
    >0: b-a -> c-a は反時計回り
    <0: b-a -> c-a は時計回り
    =0: 3点は同一直線上
    """
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

# def on_segment(a, b, c):
#     return (
#         min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and
#         min(a[1], b[1]) <= c[1] <= max(a[1], b[1])
#     )

def segments_intersect_2d(p1, p2, q1, q2):
    """
    p1-p2 と q1-q2 が交差するか（端点を含む）
    p1-p2 を基準にして、q1とq2の位置関係を判定(o1, o2)
    q1-q2 を基準にして、p1とp2の位置関係を判定(o3, o4)
    それぞれ逆向きであれば交差している
    """
    o1 = orient(p1, p2, q1)
    o2 = orient(p1, p2, q2)
    o3 = orient(q1, q2, p1)
    o4 = orient(q1, q2, p2)

    if o1*o2 < 0 and o3*o4 < 0:
        return True
    return False

# 2. 交点位置（パラメータ t, s）
def segment_intersection_params(p1, p2, q1, q2):
    """
    p(t) = p1 + t*(p2-p1)
    q(s) = q1 + s*(q2-q1)
    として、p(t) = q(s)
    を満たす t, s を求める（連立方程式）
    ( (p2-p1, -(q2-q1)) (t,s)^T   = (q1-p1) )
    これがそれぞれ図式における交点の位置を表す
    """
    p1 = np.array(p1); p2 = np.array(p2)
    q1 = np.array(q1); q2 = np.array(q2)

    # 上のr連立方程式を行列形式で表す
    dp = p2 - p1
    dq = q2 - q1

    A = np.array([dp, -dq]).T # Tは転置 (Pythonの行列は行ベクトルなので、列ベクトルにするために転置)
    b = q1 - p1

    # 行列式が小さい場合は解なし（平行で交点なし）とみなす
    if abs(np.linalg.det(A)) < 1e-10:
        return None

    t, s = np.linalg.solve(A, b)
    return t, s

# 3. crossing の over / under 判定（3D）
def crossing_over_under(p1, p2, q1, q2, t, s, projection_vector=np.array([0, 0, 1])):
    """
    入力は3次元数ベクトル(座標)
    上のsegment_intersection_paramsで求めた t, s を使って、
    p(t) と q(s) の z 座標を比較して、どちらが上かを判定
    TODO: 射影の方向を変える場合はこの関数をなおす必要があるかも
    """

    p = p1 + t*(p2 - p1)
    q = q1 + s*(q2 - q1)

    if np.dot(p, projection_vector) > np.dot(q, projection_vector):
        return "p_over"
    else:
        return "q_over"

# 4. crossing の符号（±1）
def crossing_sign(p1, p2, q1, q2, over, projection_vector=np.array([0, 0, 1])):
    """
    入力は3次元数ベクトル(座標)
    p1-p2 と q1-q2 の外積を計算して、符号を判定
    """

    dp = p2 - p1
    dq = q2 - q1
    

    if over == "p_over":
        v_over = dp
        v_under = dq
    else:
        v_over = dq
        v_under = dp

    cross = np.cross(v_over, v_under)

    # 射影方向に沿った成分の符号で判定
    return +1 if np.dot(cross, projection_vector) > 0 else -1
    
# 5. 全体：交点検出関数
def find_crossings(curves, projection_vector=np.array([0, 0, 1])):
    crossings = []

    # 射影方向を指定 # TODO: これも関数の引数にして、射影の方向を変えられるようにする
    projected_curves = [project_to_2D(curve, projection_vector) for curve in curves]

    # 全線分リスト
    # (曲線番号, 線分番号, 始点座標, 終点座標) のタプルのリスト
    segments = []
    for ci, curve in enumerate(curves):
        curve_2d = projected_curves[ci]
        for i in range(len(curve)-1):
            segments.append((ci, i, curve[i], curve[i+1], curve_2d[i], curve_2d[i+1]))

    
    
    # 全ペアチェック
    for i in range(len(segments)):
        for j in range(i+1, len(segments)):
            ci1, si1, p1, p2, p1_2d, p2_2d = segments[i]
            ci2, si2, q1, q2, q1_2d, q2_2d = segments[j]

            # 同じ曲線の隣接は無視（重要）
            if ci1 == ci2 and abs(si1 - si2) <= 1:
                continue

            # 2D射影はループ外で前計算済み（segments に保持）

            if not segments_intersect_2d(p1_2d, p2_2d, q1_2d, q2_2d):
                continue

            params = segment_intersection_params(p1_2d, p2_2d, q1_2d, q2_2d)
            if params is None:
                continue

            t, s = params

            # segments_intersect_2dで交差していると判定された場合、t, s は [0, 1] の範囲にあるはず
            # ただし、数値誤差のために範囲外になる可能性があるので、ここでチェックしておく
            if not (0 <= t <= 1 and 0 <= s <= 1):
                continue

            over = crossing_over_under(p1, p2, q1, q2, t, s, projection_vector=projection_vector)
            sign = crossing_sign(p1, p2, q1, q2, over, projection_vector=projection_vector)

            crossings.append({
                "segments": (i, j),
                "t": t,
                "s": s,
                "over": over,
                "sign": sign
            })

    return crossings



# state（A/B smoothing）
# 2. 全stateの生成
import itertools

def generate_states(n):
    """
    n個の交点に対する全てのstateを生成
    各stateは +1 (A) / -1 (B)
    """
    return list(itertools.product([+1, -1], repeat=n))

# 3. σ(S) の計算
def sigma(state):
    return sum(state)

# 5. A/B smoothing
def apply_smoothing(crossings, state):
    """
    crossings と state から
    接続情報（グラフ）を作る
    state: (1, -1, 1, ...) のタプル
    for state in states: みたいに取り出して使いそう
    """
    connections = []

    for i, c in enumerate(crossings):
        label = state[i]  # +1 or -1

        seg1, seg2 = c["segments"]

        if label == +1:
            # A smoothing
            connections.append((seg1, seg2, "A"))
        else:
            # B smoothing
            connections.append((seg1, seg2, "B"))

    return connections




# ============================================================
# Jones Polynomial Calculation
# ============================================================

# 1. Laurent 多項式の加算・乗算
#    {exp(何次の項): coeff(係数), ・・・} の辞書形式で多項式を表す
def laurent_add(p1, p2):
    """
    指数を整数（Aの冪）で持つ Laurent 多項式の和。
    p1, p2 は {exp: coeff} の辞書形式
    """
    result = dict(p1)
    for exp, coeff in p2.items():
        result[exp] = result.get(exp, 0) + coeff
    return {exp: coeff for exp, coeff in result.items() if coeff != 0}


def laurent_mul(p1, p2):
    """
    指数を整数（Aの冪）で持つ Laurent 多項式の積。
    p1, p2 は {exp: coeff} の辞書形式
    """
    result = {}
    for exp1, coeff1 in p1.items():
        for exp2, coeff2 in p2.items():
            exp = exp1 + exp2
            result[exp] = result.get(exp, 0) + coeff1 * coeff2
    return {exp: coeff for exp, coeff in result.items() if coeff != 0}


def laurent_pow(base, n):
    """
    Laurent 多項式の非負整数冪。
    p1, p2 は {exp: coeff} の辞書形式
    """
    if n == 0:
        return {0: 1}
    result = {0: 1}
    for _ in range(n):
        result = laurent_mul(result, base)
    return result


# 2. Kauffman bracket の計算
def _build_event_order(crossings):
    """
    交点がどの順番で曲線上で出てくるかを返す関数(各交点2回ずつ)

    戻り値         : [(crossing_index, branch_index), ...]
    crossing_index: 何個目の交点か (0,1,2, ...)
    branch_index  : その交点の1回目/2回目 (0 or 1)

    例: [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)]
    """
    events = [] # (position(曲線パラメータ), crossing_index, branch_index) のリスト
    for crossing_index, crossing in enumerate(crossings):
        seg1, seg2 = crossing["segments"]
        t = float(crossing["t"])
        s = float(crossing["s"])

        # 曲線上の位置を表すために、seg + t という形で position を計算する。seg は整数、t は [0,1] の小数なので、seg+t
        # 同じsegment上の交点があっても、tの値で順序が決まる
        events.append((float(seg1) + t, crossing_index, 0))
        events.append((float(seg2) + s, crossing_index, 1))

    # position でソートすると、曲線上の遭遇順が得られ、arc_map（次にどこへ進むか）を作れる
    events.sort(key=lambda item: item[0])
    return [(crossing_index, branch_index) for _, crossing_index, branch_index in events]


def count_state_cycles_by_orbits(crossings, state): # なぜcrossings, stateだけで計算できる？
    """
    smoothing 後の state ごとに cycle 数を数える関数
    「置換の軌道数」で数えている

    1) 曲線に沿う接続（arc）
    2) 各 crossing の smoothing 接続（A/B）
    を交互にたどる写像 perm を作り、perm の軌道数を cycle 数とする。

    この関数が仕事しすぎている。えらい。
    """

    # 交点がない場合は、曲線全体が1つのcycleなので、1を返す
    n_crossings = len(crossings)
    if n_crossings == 0:
        return 1

    # crossingの中に何番目のsegments かの情報が入っているから、そこから元々どう繋がっているかを復元できる
    # TODO：kauffman_bracketのループのたびに同じ計算をしているから、引数として _build_event_order(crossings) の結果を渡してあげたほうが良さそう
    ordered_events = _build_event_order(crossings)
    n_events = len(ordered_events)

    # half-edge ID を割り当てる
    # halfedge_id = {(crossing_index, branch_index, "in"|"out"): index, ...}
    # TODO：kauffman_bracketのループのたびに同じ計算をしているから、関数の外に出した方が良さそう
    halfedge_id = {}
    next_id = 0
    # 端点に名前（index）をつけていっているイメージ
    for event in ordered_events:
        crossing_index, branch_index = event
        halfedge_id[(crossing_index, branch_index, "in")] = next_id # 交点に入る(交点に向かう)半辺
        next_id += 1
        halfedge_id[(crossing_index, branch_index, "out")] = next_id # 交点から出る(交点から離れる)半辺
        next_id += 1

    n_halfedges = next_id

    # arc_map: 曲線に沿って out -> 次の in
    arc_map = {} # Lのこと  # TODO：kauffman_bracketのループのたびに同じ計算をしているから、関数の外に出した方が良さそう
    for i, (crossing_index, branch_index) in enumerate(ordered_events):
        next_crossing_index, next_branch_index = ordered_events[(i + 1) % n_events] # 次のイベント（曲線上の次の交点）を取得。最後のイベントの次は最初のイベントに戻るように % n_events している

        out_id = halfedge_id[(crossing_index, branch_index, "out")] # ここで一つ目のoutを指定しているから０でなく1スタート
        in_next_id = halfedge_id[(next_crossing_index, next_branch_index, "in")]

        arc_map[out_id] = in_next_id
        arc_map[in_next_id] = out_id  # 逆写像も入れて全域化 # これによって互換にしている

    # 例: {1: 2, 2: 1, 3: 4, 4: 3, 5: 6, 6: 5, 7: 8, 8: 7, 9: 10, 10: 9, 11: 0, 0: 11}

    # smooth_map: crossing 内の接続（A/B）
    smooth_map = {} # Sのこと
    for crossing_index, label in enumerate(state):
        in0 = halfedge_id[(crossing_index, 0, "in")]
        out0 = halfedge_id[(crossing_index, 0, "out")]
        in1 = halfedge_id[(crossing_index, 1, "in")]
        out1 = halfedge_id[(crossing_index, 1, "out")]

        # 論文の向き付けに合わせるため、交点符号でA/Bの局所対応を切り替える。
        """
        ＼　／            |    |        _____
        　／　 に対して、A: |   |      B:      
        ／　＼            |    |        _____
        右上から左下に向かうのがin0->out0、左上から右下に向かうのがin1->out1とする。
        """
        pattern_1 = ((in0, out1), (out0, in1))
        pattern_2 = ((in0, in1), (out0, out1))

        # 交点とsmoothingの対応付け
        crossing_sign_value = crossings[crossing_index]["sign"]
        if crossing_sign_value > 0:
            pairs = pattern_1 if label == +1 else pattern_2 # crossing の符号が正なら、smoothingA(label=+1)は pattern_1、smoothingB(label=-1)は pattern_2を割り当てる
        else:
            pairs = pattern_2 if label == +1 else pattern_1 # crossing の符号が負なら、向きを正の方向に90度回転するので、smoothingA(label=+1)は pattern_2、smoothingB(label=-1)は pattern_1を割り当てる

        # 互換を作る
        for left, right in pairs:
            smooth_map[left] = right
            smooth_map[right] = left
    

    # 置換 perm = arc_map ∘ smooth_map # L ∘ S
    perm = {halfedge: arc_map[smooth_map[halfedge]] for halfedge in range(n_halfedges)}

    # perm の軌道数
    visited = set()
    orbits = [] # 置換の軌道を保持するリスト（デバッグ用）
    orbit_count = 0
    for start in range(n_halfedges):
        if start in visited:
            continue
        orbit_count += 1
        current = start # a
        L_current = arc_map[start] # L(a)
        orbit = [] # Orb_s(a) U Orb_s(L(a)) 
        while current not in visited:
            visited.add(current)
            visited.add(L_current)
            orbit.append(current) # Orb_s(a)
            orbit.append(L_current) # Orb_s(L(a)) 
            current = perm[current]
            L_current = perm[L_current]
        orbits.append(orbit)

    # 半辺（in/out）を状態空間にしているため、1つの幾何学的 cycle を2回数えている。
    # したがって cycle 数は軌道数の半分。
    # print(orbits,len(orbits))
    return len(orbits)


def kauffman_bracket(crossings):
    """
    Kauffman bracket <D> を A 変数で返す。

    <D> = Σ_s A^{σ(s)} (-A^2 - A^{-2})^{|s|-1}
    ここで |s| は smoothing 後の cycle 数（置換の軌道数で計算）。

    論文に合わせてこのカウフマンかっこの時点で -A^2 - A^-2 で割ってある。
    """
    n_crossings = len(crossings)
    if n_crossings == 0:
        return {0: 1}

    states = generate_states(n_crossings)
    d_poly = {2: -1, -2: -1}  # -A^2 - A^-2
    bracket = {}

    for state in states:
        sigma_s = sigma(state)
        cycle_count = count_state_cycles_by_orbits(crossings, state) # この関数が仕事しすぎている。えらい。

        state_poly = {sigma_s: 1} # A^{σ(s)}
        state_poly = laurent_mul(state_poly, laurent_pow(d_poly, cycle_count - 1))
        # print(sigma_s,format_jones_polynomial(state_poly))
        bracket = laurent_add(bracket, state_poly)

    return bracket


# 3. Jones 多項式への正規化と変数変換
def _normalize_bracket_to_jones_in_A(bracket_A, crossings):
    """
    (-A)^(-3w(D)) <D> 
    ここでねじれを解消している ((-A)^(-3w(D))をかけている)
    """
    writhe = int(sum(int(crossing["sign"]) for crossing in crossings))
    prefactor = {(-3) * writhe: int((-1) ** (3 * writhe))}
    return laurent_mul(prefactor, bracket_A)


def _convert_A_poly_to_t_poly(poly_A):
    """
    A = t^(-1/4) を代入して t 多項式へ変換。
    指数が整数にならない場合は (numerator, 4) キーで保持。
    """
    poly_t = {}
    for a_exp, coeff in poly_A.items():
        t_num = -a_exp
        if t_num % 4 == 0:
            key = t_num // 4
        else:
            common = gcd(abs(t_num), 4)
            key = (t_num // common, 4 // common)
        poly_t[key] = poly_t.get(key, 0) + coeff
    return {exp: coeff for exp, coeff in poly_t.items() if coeff != 0}


def jones_polynomial(curves, projection_vector=np.array([0, 0, 1])):
    """
    Jones polynomial を t 変数の係数辞書で返す。
    curves: [np.array([[x,y,z], ...]), ...] のリスト
    """
    crossings = find_crossings(curves, projection_vector=projection_vector)

    bracket_A = kauffman_bracket(crossings)
    # print(f"\nKauffman bracket (A variable): {format_jones_polynomial(bracket_A)}")
    normalized_A = _normalize_bracket_to_jones_in_A(bracket_A, crossings)
    # print(f"\nNormalized bracket (A variable): {format_jones_polynomial(normalized_A)}")
    return _convert_A_poly_to_t_poly(normalized_A)


def format_jones_polynomial(poly, use_latex=False):
    """
    結果を表示用の文字列に整形
    Format Jones polynomial for display.
    
    Args:
        poly: Polynomial dict {q_exp: coefficient}
        use_latex: If True, return LaTeX format; else readable string
    
    Returns:
        Formatted string
    """
    if not poly:
        return "0" if not use_latex else "0"
    
    terms = []
    for exp in sorted(poly.keys(), key=lambda x: (x if isinstance(x, int) else x[0]), reverse=True):
        coeff = poly[exp]
        
        if isinstance(exp, tuple):
            # Fractional exponent
            num, denom = exp
            if use_latex:
                exp_str = f"^{{-{num}/{denom}}}" if num > 0 else f"^{{{num}/{denom}}}"
            else:
                exp_str = f"^({num}/{denom})"
        else:
            # Integer exponent
            if use_latex:
                exp_str = f"^{{{exp}}}" if exp != 0 else ""
            else:
                exp_str = f"^{exp}" if exp != 0 else ""
        
        if coeff == 1:
            term = f"t{exp_str}"
        elif coeff == -1:
            term = f"-t{exp_str}"
        else:
            term = f"{coeff}t{exp_str}"
        
        terms.append(term)
    
    result = " + ".join(terms).replace(" + -", " - ")
    return result

# ============================================================
# ============================================================


# 射影方向を変えようという試み

def orthonormal_basis(vector):
    vector = vector / np.linalg.norm(vector)

    # vector と直交する適当なベクトルを作る
    if abs(vector[0]) < 0.9:
        a = np.array([1, 0, 0])
    else:
        a = np.array([0, 1, 0])

    e1 = np.cross(vector, a)
    e1 = e1 / np.linalg.norm(e1)

    e2 = np.cross(vector, e1)

    return e1, e2


def project_to_2D(curve, vector):
    """
    3D点または3D点群を、vector 方向に射影して2D座標へ変換する。
    - 入力が (3,) のときは出力 (2,)
    - 入力が (N,3) のときは出力 (N,2)
    """
    vector = vector / np.linalg.norm(vector)
    e1, e2 = orthonormal_basis(vector)

    points = np.asarray(curve)
    is_single_point = points.ndim == 1
    if is_single_point:
        points = points[None, :]

    # 射影
    proj = points - np.outer(points @ vector, vector) # @は行列積、np.outerは外積（ベクトルの成分ごとの積）を計算する関数。points @ vector は (N,3) @ (3,) で (N,) になる。これを vector に沿った成分に変換するために np.outer を使っている。結果は (N,3) になる。

    # 2次元座標に変換
    u = proj @ e1
    w = proj @ e2
    projected = np.column_stack([u, w])

    if is_single_point:
        return projected[0]
    return projected


def generate_unit_sphere_points(n_points, seed=None):
    """
    Generates N points uniformly sampled on a unit sphere in 3D.
    授業で作ってたやつ
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate random points in 3D space
    points = np.random.randn(n_points, 3)

    # Normalize points to lie on the unit sphere
    norms = np.linalg.norm(points, axis=1)
    unit_points = points / norms[:, np.newaxis]
    return unit_points

# --- Configuration ---
# N_POINTS = 10  # Number of points in the 3D point cloud
# RANDOM_SEED = 42 # Fixed random seed for reproducibility
# sphere_points = generate_unit_sphere_points(N_POINTS,RANDOM_SEED)

def integrated_jones_polynomial(
    curves,
    Number_of_projections=10,
    RANDOM_SEED=42,
    show_progress=True,
):
    """
    曲線のリストを入力として、Jones polynomial を計算する関数。
    交点検出から Jones polynomial の計算までを統合している。
    """
    sphere_points = generate_unit_sphere_points(Number_of_projections, RANDOM_SEED)
    poly_map = {} # projection_vector -> jones_polynomial の辞書
    progress_print = print if show_progress else (lambda *args, **kwargs: None)
    for i, projection_vector in enumerate(sphere_points):
        progress_print(i)
        jones_poly_of_v = jones_polynomial(curves, projection_vector=projection_vector)
        poly_map[tuple(projection_vector)] = jones_poly_of_v


    # 積分 
    integrated_poly = {} # 出力となる多項式
    for jones_poly in poly_map.values():
        if 0: # TODO: 測度が０になるような点を除去する方法を考える必要がある # 一番多いものだけ採用とか？
            continue
        integrated_poly = laurent_add(integrated_poly, jones_poly)

    for exp in integrated_poly:
        integrated_poly[exp] /= len(integrated_poly)

    return poly_map


def crossing_number_distribution(
    curves,
    Number_of_projections=10,
    RANDOM_SEED=42,
    show_progress=True,
):
    """Compute crossing counts for many projection directions on the unit sphere."""
    sphere_points = generate_unit_sphere_points(Number_of_projections, RANDOM_SEED)
    crossing_num_map = {}

    progress_print = print if show_progress else (lambda *args, **kwargs: None)
    for i, projection_vector in enumerate(sphere_points):
        progress_print(i)
        crossings = find_crossings(curves, projection_vector=projection_vector)
        crossing_num_map[tuple(projection_vector)] = len(crossings)

    return crossing_num_map


def plot_crossing_num_map_on_sphere(
    crossing_num_map,
    title="Crossing number classes on sphere",
):
    """Plot projection directions on a sphere, colored by crossing number."""
    if not crossing_num_map:
        raise ValueError("crossing_num_map is empty")

    n_projection_directions = len(crossing_num_map)

    grouped_points = {}
    for projection_vector, crossing_num in crossing_num_map.items():
        crossing_num = int(crossing_num)
        if crossing_num not in grouped_points:
            grouped_points[crossing_num] = []
        grouped_points[crossing_num].append(np.asarray(projection_vector, dtype=float))

    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]

    fig = go.Figure()
    for idx, crossing_num in enumerate(sorted(grouped_points.keys())):
        points = np.array(grouped_points[crossing_num])
        fig.add_trace(go.Scatter3d(
            x=points[:, 0],
            y=points[:, 1],
            z=points[:, 2],
            mode="markers",
            marker=dict(size=5, color=colors[idx % len(colors)], opacity=0.9),
            name=f"crossings={crossing_num}",
            hovertemplate=(
                "x=%{x:.3f}<br>y=%{y:.3f}<br>z=%{z:.3f}<br>"
                + f"crossings={crossing_num}"
                + "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title=f"{title} ({n_projection_directions} projection directions)",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="cube",
        ),
        legend_title="crossing number",
    )

    fig.show()
    return fig


def _canonical_poly_key(poly):
    """
    多項式dictを比較可能な不変キーへ変換する。
    例: {1: 1, -1: -1} -> ((-1, -1), (1, 1))
    """
    return tuple(sorted(poly.items(), key=lambda item: str(item[0])))


def plot_poly_map_on_sphere(poly_map, title="Jones polynomial classes on sphere"):
    """
    poly_map: {projection_vector(tuple): polynomial(dict)} を受け取り、
    同じ Jones 多項式ごとに同じ色で球面上へプロットする。
    """
    if not poly_map:
        raise ValueError("poly_map is empty")

    # 多項式ごとに点群をグルーピング
    grouped_points = {}
    for projection_vector, polynomial in poly_map.items():
        key = _canonical_poly_key(polynomial)
        if key not in grouped_points:
            grouped_points[key] = {
                "points": [],
                "label": format_jones_polynomial(polynomial)
            }
        grouped_points[key]["points"].append(np.asarray(projection_vector, dtype=float))

    # 色パレット（カテゴリ数が増えても循環）
    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ]

    fig = go.Figure()
    for index, (poly_key, info) in enumerate(grouped_points.items()):
        points = np.array(info["points"])
        fig.add_trace(go.Scatter3d(
            x=points[:, 0],
            y=points[:, 1],
            z=points[:, 2],
            mode="markers",
            marker=dict(size=5, color=colors[index % len(colors)], opacity=0.9),
            name=info["label"],
            hovertemplate=(
                "x=%{x:.3f}<br>y=%{y:.3f}<br>z=%{z:.3f}<br>"
                + "<extra>"
                + info["label"]
                + "</extra>"
            )
        ))

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="cube"
        ),
        legend_title="Jones polynomial"
    )

    fig.show()
    return fig


def launch_interactive_jones_direction_explorer(
    curves,
    poly_map,
    title="Interactive Jones polynomial explorer",
    host="127.0.0.1",
    port=8050,
    debug=False,
    run_server=True,
):
    """Launch an interactive app: click a sphere point to view its 2D knot diagram."""
    if not poly_map:
        raise ValueError("poly_map is empty")
    if not curves or len(curves) == 0:
        raise ValueError("curves list is empty")

    try:
        import importlib

        dash_module = importlib.import_module("dash")
        Dash = getattr(dash_module, "Dash")
        Input = getattr(dash_module, "Input")
        Output = getattr(dash_module, "Output")
        dcc = getattr(dash_module, "dcc")
        html = getattr(dash_module, "html")
    except ImportError as exc:
        raise ImportError(
            "dash is required for interactive explorer. Install it with: pip install dash"
        ) from exc

    grouped_points = {}
    for projection_vector, polynomial in poly_map.items():
        key = _canonical_poly_key(polynomial)
        if key not in grouped_points:
            grouped_points[key] = {
                "points": [],
                "label": format_jones_polynomial(polynomial),
            }
        grouped_points[key]["points"].append(np.asarray(projection_vector, dtype=float))

    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]

    sphere_fig = go.Figure()
    for index, (_poly_key, info) in enumerate(grouped_points.items()):
        points = np.array(info["points"])
        sphere_fig.add_trace(go.Scatter3d(
            x=points[:, 0],
            y=points[:, 1],
            z=points[:, 2],
            mode="markers",
            marker=dict(size=5, color=colors[index % len(colors)], opacity=0.9),
            name=info["label"],
            customdata=points,
            hovertemplate=(
                "x=%{x:.3f}<br>y=%{y:.3f}<br>z=%{z:.3f}<br>"
                + "<extra>"
                + info["label"]
                + "</extra>"
            ),
        ))

    n_projection_directions = len(poly_map)
    sphere_fig.update_layout(
        title=f"{title} ({n_projection_directions} projection directions)",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="cube",
        ),
        legend_title="Jones polynomial",
        clickmode="event+select",
    )

    first_direction = np.asarray(next(iter(poly_map.keys())), dtype=float)
    first_diagram = project_to_2D(curves[0], first_direction)
    diagram_fig = go.Figure(
        data=[
            go.Scatter(
                x=first_diagram[:, 0],
                y=first_diagram[:, 1],
                mode="lines+markers",
                marker=dict(size=5, color="#1f77b4", opacity=0.85),
                line=dict(color="#1f77b4", width=1),
            )
        ]
    )
    diagram_fig.update_layout(
        title=(
            "2D diagram (initial direction): "
            f"({first_direction[0]:.3f}, {first_direction[1]:.3f}, {first_direction[2]:.3f})"
        ),
        xaxis_title="X",
        yaxis_title="Y",
        yaxis_scaleanchor="x",
        yaxis_scaleratio=1,
        showlegend=False,
    )

    app = Dash(__name__)
    app.layout = html.Div(
        [
            html.H3("Click a point on the sphere to view the projected 2D knot diagram"),
            html.Div(
                [
                    dcc.Graph(
                        id="sphere-plot",
                        figure=sphere_fig,
                        style={"height": "72vh", "width": "100%"},
                    ),
                    dcc.Graph(
                        id="diagram-plot",
                        figure=diagram_fig,
                        style={"height": "72vh", "width": "100%"},
                    ),
                ],
                style={
                    "display": "flex",
                    "flexDirection": "row",
                    "gap": "12px",
                    "alignItems": "stretch",
                },
            ),
        ]
    )

    @app.callback(
        Output("diagram-plot", "figure"),
        Input("sphere-plot", "clickData"),
    )
    def _update_diagram(click_data):
        if not click_data or "points" not in click_data or not click_data["points"]:
            return diagram_fig

        point_info = click_data["points"][0]
        direction = point_info.get("customdata")
        if direction is None:
            direction = [point_info["x"], point_info["y"], point_info["z"]]

        direction = np.asarray(direction, dtype=float)
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm

        projected = project_to_2D(curves[0], direction)
        figure = go.Figure(
            data=[
                go.Scatter(
                    x=projected[:, 0],
                    y=projected[:, 1],
                    mode="lines+markers",
                    marker=dict(size=5, color="#1f77b4", opacity=0.85),
                    line=dict(color="#1f77b4", width=1),
                )
            ]
        )
        figure.update_layout(
            title=(
                "2D diagram for selected direction: "
                f"({direction[0]:.3f}, {direction[1]:.3f}, {direction[2]:.3f})"
            ),
            xaxis_title="X",
            yaxis_title="Y",
            yaxis_scaleanchor="x",
            yaxis_scaleratio=1,
            showlegend=False,
        )
        return figure

    if run_server:
        run_fn = getattr(app, "run", None)
        if run_fn is None:
            run_fn = app.run_server
        run_fn(host=host, port=port, debug=debug)

    return app


def plot_distinct_jones_poly_diagrams(curves, poly_map, title="Jones polynomial diagrams by projection direction"):
    """
    異なるJones多項式ごとに、その多項式が対応する射影方向を1つ選んで、
    その方向への2D図式を表示する。
    
    Args:
        curves: [np.array([[x,y,z], ...]), ...] のリスト
        poly_map: {projection_vector(tuple): polynomial(dict)} 
                  integrated_jones_polynomial() からの出力
        title: 図のタイトル
    """
    if not poly_map:
        raise ValueError("poly_map is empty")
    
    if not curves or len(curves) == 0:
        raise ValueError("curves list is empty")
    
    # 異なる多項式ごとに、最初の方向を記録
    poly_to_direction = {}
    for direction_tuple, polynomial in poly_map.items():
        poly_key = _canonical_poly_key(polynomial)
        if poly_key not in poly_to_direction:
            # 多項式キーをそのまま保持しつつ、対応する方向を記録
            direction_vector = np.asarray(direction_tuple, dtype=float)
            direction_vector = direction_vector / np.linalg.norm(direction_vector)
            poly_to_direction[poly_key] = {
                "direction": direction_vector,
                "polynomial": polynomial,
                "label": format_jones_polynomial(polynomial)
            }
    
    # 各異なる多項式について図式を表示
    for poly_idx, (poly_key, info) in enumerate(poly_to_direction.items(), start=1):
        direction = info["direction"]
        jp_label = info["label"]
        
        # 最初の曲線を指定方向に2D射影
        diagram_2d = project_to_2D(curves[0], direction)
        
        fig = go.Figure(data=[go.Scatter(
            x=diagram_2d[:, 0],
            y=diagram_2d[:, 1],
            mode='markers',
            marker=dict(
                size=6,
                color='blue',
                opacity=0.85
            )
        )])
        
        fig.update_layout(
            title=f"Diagram {poly_idx}: {jp_label}<br>Projection direction: ({direction[0]:.3f}, {direction[1]:.3f}, {direction[2]:.3f})",
            xaxis_title='X',
            yaxis_title='Y',
            yaxis_scaleanchor='x',
            yaxis_scaleratio=1,
            showlegend=False
        )
        
        fig.show()
    
    print(f"\nDisplayed {len(poly_to_direction)} distinct Jones polynomials")


# ============================================================================
# VRフィルトレーション (Vietoris-Rips Filtration)
# 論文 Section 3.2 に基づく実装
# ============================================================================

def segment_hausdorff_distance(segment_a, segment_b):
    """
    2つのセグメント（点列）間のHausdorff距離を計算する。
    セグメントは二つの端点で指定される線分。

    d_H(A, B) = max( sup_{a in A} inf_{b in B} ||a-b||,
                     sup_{b in B} inf_{a in A} ||a-b|| )
    """
    a = np.asarray(segment_a, dtype=float)
    b = np.asarray(segment_b, dtype=float)

    # 全点間距離行列 (|A|, |B|)
    pairwise = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2) # こいつ何しとるかわからんけど多分めちゃくちゃ偉い。

    # directed Hausdorff: A -> B, B -> A
    directed_ab = np.max(np.min(pairwise, axis=1))
    directed_ba = np.max(np.min(pairwise, axis=0))
    return float(max(directed_ab, directed_ba))


def distance_matrix(segments):
    """
    セグメント間の距離行列を計算
    
    各セグメント li, lj 間の距離をHausdorff距離で計算する。
    
    Parameters
    ----------
    segments : list of np.ndarray
        n個のセグメント。各セグメントは (m_i, 3) 形の座標配列
        
    Returns
    -------
    distances : np.ndarray
        (n, n) 対称距離行列
    """
    n = len(segments)
    distances = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i+1, n):
            h_dist = segment_hausdorff_distance(segments[i], segments[j])
            distances[i, j] = h_dist
            distances[j, i] = h_dist
    
    return distances



def build_vietoris_rips_complex(distances, radius, max_dimension=2):
    """
    Vietoris-Rips複体を指定された半径で構築
    TODO: 指定した次元で計算できるように一般化できないか？
    三次元では少なすぎるのでは？単体に対するセグメントがどんなものになるか考える。
    と言うよりセグメントは線分ではなく、折れ線のことと考えるべき？
    
    Parameters
    ----------
    distances : np.ndarray
        (n, n) セグメント間距離行列
    radius : float
        VR複体の半径パラメータ
    max_dimension : int
        構築する最大次元（0,1,2...）。
        計算量削減のため、まずは1（辺まで）を推奨。
        
    Returns
    -------
    simplices : dict
        次元 -> シンプレックスリスト のマッピング
        各シンプレックスは頂点インデックスのタプル
    """
    n = len(distances)
    max_dimension = int(max_dimension)
    if max_dimension < 0:
        raise ValueError("max_dimension must be >= 0")

    simplices = {d: [] for d in range(max_dimension + 1)}
    
    # 0-シンプレックス（頂点）
    if max_dimension >= 0:
        for i in range(n):
            simplices[0].append((i,))
    
    # 1-シンプレックス（エッジ）
    if max_dimension >= 1:
        for i in range(n):
            for j in range(i+1, n):
                if distances[i, j] <= radius:
                    simplices[1].append((i, j))
    
    # 2-シンプレックス（三角形）
    if max_dimension >= 2:
        for i in range(n):
            for j in range(i+1, n):
                for k in range(j+1, n):
                    # 全ペアが radius 以下の距離
                    if (distances[i, j] <= radius and 
                        distances[i, k] <= radius and 
                        distances[j, k] <= radius):
                        simplices[2].append((i, j, k))
    
    return simplices


def get_facets(simplices, dimension=None):
    """
    単体複体のファセット（包含関係での極大単体）を抽出する。

    facet は「どのより高次の単体にも真に含まれない単体」を意味する。
    dimension を指定した場合は、極大単体のうち指定次元のものだけを返す。
    
    Parameters
    ----------
    simplices : dict
        build_vietoris_rips_complex の出力
    dimension : int or None
        指定した場合、その次元の facet だけを返す。
        None の場合は全 facet を返す。
        
    Returns
    -------
    facets : list
        ファセット（極大単体）のリスト
    """
    # 次元ごとの候補を用意し、上位次元から下へ向けて候補を削る
    candidate_by_dim = {
        dim: list(simplices.get(dim, []))
        for dim in sorted(simplices.keys(), reverse=True)
    }
    print(candidate_by_dim)

    # すでに facet と確定した上位次元単体の集合表現
    higher_facet_sets = []
    facets_by_dim = {}

    for dim in sorted(candidate_by_dim.keys(), reverse=True):
        current_candidates = candidate_by_dim[dim]
        if not current_candidates:
            continue

        # 同じ次元同士は包含しないので、比較は上位次元 facet だけで十分
        remaining = []
        for simplex in current_candidates:
            simplex_set = set(simplex)
            if not any(simplex_set.issubset(higher_facet) for higher_facet in higher_facet_sets): #一番上の次元に関しては higher_facet_sets は空だから、すべての simplex が remaining に入ることになる。
                remaining.append(simplex)

        facets_by_dim[dim] = remaining
        new_higher_facet_sets = [set(simplex) for simplex in remaining]
        higher_facet_sets.extend(new_higher_facet_sets)

        # 確定した facet の部分単体は下位次元の候補から除外して計算量を抑える。
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


def compute_critical_values(distances, max_iterations=None):
    """
    Vietoris-Rips複体の臨界値を計算
    
    臨界値は、複体の構造が変わる半径値
    この値たちだけでフィルトレーションを構築すれば、同じホモロジーが得られる。
    
    Parameters
    ----------
    distances : np.ndarray
        セグメント間距離行列
    max_iterations : int, optional
        最大反復数（デフォルト: 距離の一意値数）
        
    Returns
    -------
    critical_values : list
        昇順の臨界値リスト
    """
    # 距離行列から0でない値を抽出し、ソート
    unique_distances = np.unique(distances[distances > 0])
    
    if max_iterations is not None:
        unique_distances = unique_distances[:max_iterations]
    
    return sorted(unique_distances)


def build_vr_filtration(segments, max_radius=None, max_stages=None, max_dimension=2):
    """
    セグメント集合からVRフィルトレーション写像を構築
    
    Return: 単体 -> 発生時刻（半径）の写像
    
    Parameters
    ----------
    segments : list of np.ndarray
        セグメント集合
    max_radius : float, optional
        最大半径（デフォルト: 距離行列の最大値の少し先）
    max_stages : int, optional
        フィルトレーション段数の上限。指定時は臨界値を間引く。
    max_dimension : int
        構築する最大次元。計算量削減のため、まずは1を推奨。
        
    Returns
    -------
    simplex_birth_time_map : dict
        {simplex(tuple[int,...]): birth_radius(float)}
    """
    # ステップ1: 距離行列を計算
    distances = distance_matrix(segments)

    # ステップ2: 単体ごとの発生時刻を直接計算
    # 0次単体は時刻 0 で既に存在
    simplex_birth_time_map = {}
    n_vertices = len(segments)
    max_dimension = int(max_dimension)
    if max_dimension < 0:
        raise ValueError("max_dimension must be >= 0")

    for i in range(n_vertices):
        simplex_birth_time_map[(i,)] = 0.0

    # 1次以上の単体は「含まれる辺長の最大値」を発生時刻とする
    # （VR複体で simplex が初めて出現する最小半径）
    for simplex_size in range(2, max_dimension + 2):
        for simplex in itertools.combinations(range(n_vertices), simplex_size):
            birth = 0.0
            for i, j in itertools.combinations(simplex, 2):
                birth = max(birth, float(distances[i, j]))

            if max_radius is not None and birth > float(max_radius):
                continue

            simplex_birth_time_map[tuple(simplex)] = birth

    # max_stages が指定された場合は、発生時刻を代表半径へ丸める
    # （増大列側で段数を間引いた場合に対応する写像表現）
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


def _build_filtration_from_birth_time_map(simplex_birth_time_map):
    """
    単体 -> 発生時刻の写像から、増大列としてのフィルトレーションを復元する。
    """
    if not simplex_birth_time_map:
        return []

    normalized = {
        tuple(sorted(simplex)): float(radius)
        for simplex, radius in simplex_birth_time_map.items()
    }
    radii = sorted(set(normalized.values()))
    vr_filtration = []

    for radius in radii:
        simplices = {}
        for simplex, birth in normalized.items():
            if birth <= radius:
                dim = len(simplex) - 1
                simplices.setdefault(dim, []).append(simplex)

        if simplices:
            max_dim = max(simplices.keys())
            for dim in range(max_dim + 1):
                simplices.setdefault(dim, [])

        for dim in simplices:
            simplices[dim] = sorted(simplices[dim])

        facets = get_facets(simplices, dimension=None) if simplices else []
        vr_filtration.append({
            'radius': float(radius),
            'simplices': simplices,
            'facets': facets,
            'facets_1d': [facet for facet in facets if len(facet) == 2],
            'facets_2d': [facet for facet in facets if len(facet) == 3],
        })

    return vr_filtration


def build_simplex_birth_time_map(vr_filtration):
    """
    フィルトレーション写像（単体 -> 発生時刻）を構成する。

    各単体 simplex に対して、
      f(simplex) = その単体が最初に出現した半径
    を返す。

    Parameters
    ----------
    vr_filtration : list of dict または dict
        list の場合: 各段に 'radius' と 'simplices' を持つ増大列
        dict の場合: build_vr_filtration の出力

    Returns
    -------
    birth_time_map : dict
        {simplex(tuple[int,...]): birth_radius(float)}
    """
    if isinstance(vr_filtration, dict):
        return {
            tuple(sorted(simplex)): float(radius)
            for simplex, radius in vr_filtration.items()
        }

    birth_time_map = {}

    for stage in vr_filtration:
        radius = float(stage['radius'])
        simplices_by_dim = stage['simplices']

        for dim in sorted(simplices_by_dim.keys()):
            for simplex in simplices_by_dim[dim]:
                simplex_key = tuple(sorted(simplex))
                if simplex_key not in birth_time_map:
                    birth_time_map[simplex_key] = radius

    return birth_time_map


def extract_facet_birth_death_pairs(vr_filtration, dimension=None):
    """
        facet 的な生成消滅対（birth-death pair）を返す。

        手順:
        - 単体を次元ごと（低次元→高次元）かつ birth 昇順で走査する
        - 各単体 simplex が出現した時刻 birth(simplex) を、
            simplex に真に含まれる face の death 候補として与える
        - すでに death が確定している face は更新しない（最初の1回だけ設定）

    Parameters
    ----------
    vr_filtration : list of dict または dict
        list の場合: 各段に 'radius' と 'simplices' を持つ増大列
        dict の場合: build_vr_filtration の出力（単体 -> 発生時刻）
    dimension : int or None
        指定した場合、その次元の単体だけを返す。
        None の場合は全次元を返す。

    Returns
    -------
    pairs_by_dimension : dict[int, list[dict]]
        {dimension: [{'simplex': tuple,
                      'birth': float,
                      'death': float | None,
                      'lifetime': float | None}, ...]}
        death=None は最後まで facet のまま（有限段では消滅しない）を表す。
    """
    birth_time_map = build_simplex_birth_time_map(vr_filtration)
    if not birth_time_map:
        return []

    simplices = sorted(tuple(sorted(simplex)) for simplex in birth_time_map.keys())
    max_size = max(len(simplex) for simplex in simplices)
    simplices_by_size = {size: [] for size in range(1, max_size + 1)}
    for simplex in simplices:
        simplices_by_size[len(simplex)].append(simplex)

    for size in simplices_by_size:
        simplices_by_size[size].sort(
            key=lambda simplex: (float(birth_time_map[simplex]), simplex)
        )

    death_map = {simplex: None for simplex in simplices}

    # 低次元→高次元で走査し、各高次単体の出現時刻を face の death に一度だけ割り当てる
    for size in range(2, max_size + 1):
        for simplex in simplices_by_size[size]:
            death_time = float(birth_time_map[simplex])
            for face_size in range(1, size):
                for face in itertools.combinations(simplex, face_size):
                    face = tuple(sorted(face))
                    if face in death_map and death_map[face] is None:
                        death_map[face] = death_time

    result_by_dimension = {}
    for simplex in simplices:
        simplex_dim = len(simplex) - 1
        if dimension is not None and simplex_dim != int(dimension):
            continue

        birth = float(birth_time_map[simplex])
        death = death_map[simplex]
        lifetime = (death - birth) if death is not None else None

        result_by_dimension.setdefault(simplex_dim, []).append({
            'simplex': simplex,
            'birth': birth,
            'death': death,
            'lifetime': lifetime,
        })

    for dim in result_by_dimension:
        result_by_dimension[dim].sort(key=lambda item: (item['birth'], item['simplex']))

    return {dim: result_by_dimension[dim] for dim in sorted(result_by_dimension.keys())}



def extract_facet_presence_from_filtration(vr_filtration, dimension=1):
    """
    VR フィルトレーション中で facet がいつ観測されたかの要約を返す。

    これは persistent homology の barcode ではない。
    ここで追っているのは、各次元の最大単体がフィルトレーション中で
    いつ最初に現れ、最後にいつ観測されたかという履歴。

    Parameters
    ----------
    vr_filtration : list of dict または dict
        list の場合: 各段に 'radius' と 'simplices' を持つ増大列
        dict の場合: build_vr_filtration の出力（単体 -> 発生時刻）
    dimension : int
        対象次元（1 = エッジ, 2 = 三角形）

    Returns
    -------
    summary : list of dicts
        各要素は {
            'facet': tuple,
            'first_seen_radius': float,
            'last_seen_radius': float,
            'presence_span': float,
            'active_stages': int
        }
    """
    if isinstance(vr_filtration, dict):
        vr_filtration = _build_filtration_from_birth_time_map(vr_filtration)

    facet_key = f'facets_{dimension}d'

    first_seen = {}
    last_seen = {}
    active_stages = {}

    for stage in vr_filtration:
        radius = stage['radius']
        for facet in stage[facet_key]:
            if facet not in first_seen:
                first_seen[facet] = radius
            last_seen[facet] = radius
            active_stages[facet] = active_stages.get(facet, 0) + 1

    summary = []
    for facet in sorted(first_seen.keys()):
        first_radius = first_seen[facet]
        last_radius = last_seen[facet]
        summary.append({
            'facet': facet,
            'first_seen_radius': first_radius,
            'last_seen_radius': last_radius,
            'presence_span': last_radius - first_radius,
            'active_stages': active_stages[facet],
        })

    return summary


def extract_barcode_from_filtration(vr_filtration, dimension=1):
    """
    旧名の互換ラッパー。

    実際には barcode ではなく、facet の出現履歴の要約を返す。
    """
    return extract_facet_presence_from_filtration(vr_filtration, dimension=dimension)


def plot_birth_death_pairs_by_dimension(
    birth_death_pairs,
    title_prefix="Birth-Death Diagram",
    show_diagonal=True,
):
    """
    birth-death pair を次元ごとに分けて可視化する。

    Parameters
    ----------
    birth_death_pairs : dict[int, list[dict]] または list of dict
        extract_facet_birth_death_pairs の出力（新形式）
        互換のため旧形式（list）も受け付ける
    title_prefix : str
        図タイトルの接頭辞
    show_diagonal : bool
        True の場合、対角線 y=x を描画する

    Returns
    -------
    figures_by_dimension : dict
        {dimension: plotly.graph_objects.Figure}
    """
    if not birth_death_pairs:
        raise ValueError("birth_death_pairs is empty")

    if isinstance(birth_death_pairs, dict):
        pairs_by_dim = {int(dim): list(pairs) for dim, pairs in birth_death_pairs.items()}
    else:
        pairs_by_dim = {}
        for pair in birth_death_pairs:
            dim = int(pair["dimension"])
            normalized_pair = {
                "simplex": pair["simplex"],
                "birth": pair["birth"],
                "death": pair["death"],
                "lifetime": pair["lifetime"],
            }
            pairs_by_dim.setdefault(dim, []).append(normalized_pair)

    figures_by_dimension = {}

    for dim in sorted(pairs_by_dim.keys()):
        pairs = pairs_by_dim[dim]
        finite_pairs = [p for p in pairs if p["death"] is not None]
        infinite_pairs = [p for p in pairs if p["death"] is None]

        finite_births = [float(p["birth"]) for p in finite_pairs]
        finite_deaths = [float(p["death"]) for p in finite_pairs]

        all_births = [float(p["birth"]) for p in pairs]
        max_axis = max(all_births) if all_births else 1.0
        if finite_deaths:
            max_axis = max(max_axis, max(finite_deaths))
        if max_axis <= 0:
            max_axis = 1.0

        infinite_y = max_axis * 1.05
        pad = max_axis * 0.08

        fig = go.Figure()

        if finite_pairs:
            fig.add_trace(go.Scatter(
                x=finite_births,
                y=finite_deaths,
                mode="markers",
                marker=dict(size=7, color="#1f77b4", opacity=0.9),
                name="finite",
                hovertemplate=(
                    "birth=%{x:.6f}<br>death=%{y:.6f}<extra>finite</extra>"
                ),
            ))

        if infinite_pairs:
            inf_births = [float(p["birth"]) for p in infinite_pairs]
            inf_deaths = [infinite_y] * len(inf_births)
            fig.add_trace(go.Scatter(
                x=inf_births,
                y=inf_deaths,
                mode="markers",
                marker=dict(size=8, symbol="x", color="#d62728", opacity=0.95),
                name="death=None (infinite)",
                hovertemplate=(
                    "birth=%{x:.6f}<br>death=∞<extra>infinite</extra>"
                ),
            ))

            fig.add_hline(
                y=infinite_y,
                line=dict(color="#d62728", dash="dot", width=1),
                annotation_text="death=∞ (表示用)",
                annotation_position="top left",
            )

        if show_diagonal:
            diag_max = max(max_axis, infinite_y)
            fig.add_trace(go.Scatter(
                x=[0.0, diag_max],
                y=[0.0, diag_max],
                mode="lines",
                line=dict(color="#7f7f7f", dash="dash"),
                name="y=x",
                hoverinfo="skip",
            ))

        fig.update_layout(
            title=f"{title_prefix} (dimension={dim})",
            xaxis_title="Birth",
            yaxis_title="Death",
            xaxis=dict(range=[0.0, max(max_axis, infinite_y) + pad]),
            yaxis=dict(range=[0.0, max(max_axis, infinite_y) + pad]),
            yaxis_scaleanchor="x",
            yaxis_scaleratio=1,
        )

        fig.show()
        figures_by_dimension[dim] = fig

    return figures_by_dimension


def print_vr_filtration_summary(vr_filtration):
    """VRフィルトレーションの概要を表示"""
    if isinstance(vr_filtration, dict):
        vr_filtration = _build_filtration_from_birth_time_map(vr_filtration)

    print("\n" + "="*70)
    print("Vietoris-Rips Filtration Summary")
    print("="*70)
    
    for stage_idx, stage in enumerate(vr_filtration):
        radius = stage['radius']
        n_vertices = len(stage['simplices'][0])
        n_edges = len(stage['facets_1d'])
        n_triangles = len(stage['facets_2d'])
        
        print(f"\nStage {stage_idx:3d}: radius = {radius:.6f}")
        print(f"  Vertices:  {n_vertices}")
        print(f"  Edges:     {n_edges}")
        print(f"  Triangles: {n_triangles}")


def segment_midpoints(segments):
    """各セグメントを代表点（中点）に変換する。"""
    points = []
    for seg in segments:
        seg = np.asarray(seg, dtype=float)
        points.append(seg.mean(axis=0))
    return np.asarray(points, dtype=float)


def pairwise_distance_matrix(points):
    """点群からユークリッド距離行列を作る。"""
    points = np.asarray(points, dtype=float)
    diff = points[:, None, :] - points[None, :, :]
    return np.linalg.norm(diff, axis=2)


def build_vr_persistence_with_homcloud(
    segments,
    maxdim=2,
    maxvalue=None,
    save_to="rips_segments.pdgm",
    save_graph=False,
):
    """
    homcloud を使って VR フィルトレーション由来のパーシステンス図を計算する。

    Parameters
    ----------
    segments : list[np.ndarray]
        セグメント列（各要素は形状 (k, 3) を想定）
    maxdim : int
        計算する最大次元
    maxvalue : float | None
        VR 計算の閾値（指定時は計算コストを削減）
    save_to : str
        pdgm ファイルの保存先
    save_graph : bool
        optimal 1-cycle 用のグラフ情報も保存するか

    Returns
    -------
    result : dict
        {
          "distance_matrix": np.ndarray,
          "pdgm_path": str,
          "diagrams": {d: {"births": np.ndarray, "deaths": np.ndarray, "essential_births": np.ndarray}}
        }
    """
    try:
        import homcloud.interface as hc  # type: ignore[import-not-found]
    except Exception as exc:
        raise RuntimeError(
            "homcloud を import できませんでした。"
            "この環境では homcloud ビルド時に CGAL ヘッダが必要です。"
            "macOS の場合は CGAL を導入してから再インストールしてください。"
        ) from exc

    points = segment_midpoints(segments)
    dmatrix = pairwise_distance_matrix(points)

    save_path = Path(save_to)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    kwargs = {
        "maxdim": int(maxdim),
        "save_to": str(save_path),
        "save_graph": bool(save_graph),
    }
    if maxvalue is not None:
        kwargs["maxvalue"] = float(maxvalue)

    pdlist = hc.PDList.from_rips_filtration(dmatrix, **kwargs)
    pdlist = hc.PDList(str(save_path)) if pdlist is None else pdlist

    diagrams = {}
    for d in range(maxdim + 1):
        pd = pdlist.dth_diagram(d)
        births = np.asarray(getattr(pd, "births"), dtype=float)
        deaths = np.asarray(getattr(pd, "deaths"), dtype=float)
        essential_births = np.asarray(getattr(pd, "essential_births", np.array([])), dtype=float)

        diagrams[d] = {
            "births": births,
            "deaths": deaths,
            "essential_births": essential_births,
        }

    return {
        "distance_matrix": dmatrix,
        "pdgm_path": str(save_path),
        "diagrams": diagrams,
    }
