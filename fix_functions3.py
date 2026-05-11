import sys

with open('functions.py', 'r') as f:
    content = f.read()

new_content = content.replace(
'''    n_halfedges = next_id

    # arc_map: 曲線に沿って out -> 次の in
    arc_map = {} # Lのこと  # TODO：kauffman_bracketのループのたびに同じ計算をしているから、関数の外に出した方が良さそう
    for i, (crossing_index, branch_index) in enumerate(ordered_events):
        next_crossing_index, next_branch_index = ordered_events[(i + 1) % n_events] # 次のイベント（曲線上の次の交点）を取得。最後のイベントの次は最初のイベントに戻るように % n_events している

        out_id = halfedge_id[(crossing_index, branch_index, "out")] # ここで一つ目のoutを指定しているから０でなく1スタート
        in_next_id = halfedge_id[(next_crossing_index, next_branch_index, "in")]

        arc_map[out_id] = in_next_id
        arc_map[in_next_id] = out_id  # 逆写像も入れて全域化 # これによって互換 にしている''',
'''    n_halfedges = next_id

    # arc_map: 曲線に沿って out -> 次の in
    arc_map = {} # Lのこと  
    for curve_events in ordered_events:
        n_events_in_curve = len(curve_events)
        for i, (crossing_index, branch_index) in enumerate(curve_events):
            next_crossing_index, next_branch_index = curve_events[(i + 1) % n_events_in_curve]

            out_id = halfedge_id[(crossing_index, branch_index, "out")]
            in_next_id = halfedge_id[(next_crossing_index, next_branch_index, "in")]

            arc_map[out_id] = in_next_id
            arc_map[in_next_id] = out_id''')

with open('functions.py', 'w') as f:
    f.write(new_content)
