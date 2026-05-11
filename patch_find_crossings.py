import re

with open('functions.py', 'r') as f:
    content = f.read()

new_content = content.replace(
'''        for k in range(len(i_intersect)):
            crossings.append({
                "segments": (int(i_intersect[k]), int(j_intersect[k])),
                "t": float(t_intersect[k]),
                "s": float(s_intersect[k]),
                "over": str(over_strs[k]),
                "sign": int(signs[k])
            })''',
'''        for k in range(len(i_intersect)):
            crossings.append({
                "segments": (int(i_intersect[k]), int(j_intersect[k])),
                "curves": (int(ci_arr[i_intersect[k]]), int(ci_arr[j_intersect[k]])),
                "t": float(t_intersect[k]),
                "s": float(s_intersect[k]),
                "over": str(over_strs[k]),
                "sign": int(signs[k])
            })''')

with open('functions.py', 'w') as f:
    f.write(new_content)
