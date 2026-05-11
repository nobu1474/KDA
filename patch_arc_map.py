import sys

with open('functions.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
with open('functions.py', 'w') as f:
    for line in lines:
        if 'def _build_event_order(crossings):' in line:
            f.write('''def _build_event_order(crossings):
    events_by_target = []
    for crossing_index, crossing in enumerate(crossings):
        seg1, seg2 = crossing["segments"]
        t = float(crossing["t"])
        s = float(crossing["s"])
        # We don't have curve index here easily, but we know segments are indices.
        # Wait, if we use seg + t, since segments are grouped by curve, 
        # as long as we don't connect across curves, we are good.
        # But we really need to know which curve each event is on.
        # Actually, the user already added "curves" to the crossings!
        curves = crossing.get("curves", (0, 0)) # fallback
        events_by_target.append((curves[0], float(seg1) + t, crossing_index, 0))
        events_by_target.append((curves[1], float(seg2) + s, crossing_index, 1))

    # Group by curve
    from collections import defaultdict
    curve_events = defaultdict(list)
    for ev in events_by_target:
        curve_events[ev[0]].append(ev)
        
    ordered = []
    for curve in sorted(curve_events.keys()):
        evs = curve_events[curve]
        evs.sort(key=lambda item: item[1])
        ordered.append([(e[2], e[3]) for e in evs])
    return ordered
''')
            skip = True
        elif skip and 'def count_state_cycles_by_orbits(crossings, state):' in line:
            skip = False
            f.write(line)
        elif not skip:
            f.write(line)
