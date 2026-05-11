import sys

with open('functions.py', 'r') as f:
    content = f.read()

new_content = content.replace(
'''    halfedge_id = {}
    next_id = 0
    # 端点に名前（index）をつけていっているイメージ
    for event in ordered_events:
        crossing_index, branch_index = event
        halfedge_id[(crossing_index, branch_index, "in")] = next_id # 交点に入る(交点に向かう)半辺
        next_id += 1
        halfedge_id[(crossing_index, branch_index, "out")] = next_id # 交点から 出る(交点から離れる)半辺
        next_id += 1''',
'''    halfedge_id = {}
    next_id = 0
    # 端点に名前（index）をつけていっているイメージ
    for curve_events in ordered_events:
        for event in curve_events:
            crossing_index, branch_index = event
            halfedge_id[(crossing_index, branch_index, "in")] = next_id
            next_id += 1
            halfedge_id[(crossing_index, branch_index, "out")] = next_id
            next_id += 1''')

with open('functions.py', 'w') as f:
    f.write(new_content)
