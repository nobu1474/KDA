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
    """Generates N points uniformly sampled on a unit sphere in 3D."""
    if seed is not None:
        np.random.seed(seed)

    # Generate random points in 3D space
    points = np.random.randn(n_points, 3)

    # Normalize points to lie on the unit sphere
    norms = np.linalg.norm(points, axis=1)
    unit_points = points / norms[:, np.newaxis]
    return unit_points

# --- Configuration ---
N_POINTS = 10  # Number of points in the 3D point cloud
RANDOM_SEED = 42 # Fixed random seed for reproducibility
sphere_points = generate_unit_sphere_points(N_POINTS,RANDOM_SEED)

def integrated_jones_polynomial(curves, sphere_points=sphere_points):
    """
    曲線のリストを入力として、Jones polynomial を計算する関数。
    交点検出から Jones polynomial の計算までを統合している。
    """
    poly_map = {} # projection_vector -> jones_polynomial の辞書
    for projection_vector in sphere_points:
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
