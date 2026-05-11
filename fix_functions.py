import re

with open('functions.py', 'r') as f:
    content = f.read()

new_content = content.replace(
'''    ordered = []
    for curve in sorted(curve_events.keys()):
        evs = curve_events[curve]
        evs.sort(key=lambda item: item[1])
        ordered.append([(e[2], e[3]) for e in evs])
    return ordered''',
'''    ordered = []
    for curve in sorted(curve_events.keys()):
        evs = curve_events[curve]
        evs.sort(key=lambda item: item[1])
        ordered.extend([(e[2], e[3]) for e in evs])
    return ordered''')

with open('functions.py', 'w') as f:
    f.write(new_content)
