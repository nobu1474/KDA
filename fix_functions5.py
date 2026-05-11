import sys

with open('functions.py', 'r') as f:
    content = f.read()

new_content = content.replace(
'''    ordered_events = _build_event_order(crossings)
    n_events = len(ordered_events)''',
'''    ordered_events = _build_event_order(crossings)''')

with open('functions.py', 'w') as f:
    f.write(new_content)
