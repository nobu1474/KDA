import functions

class Dummy: pass
def mock_crossings():
    return [{"segments": (0, 1), "t": 0.5, "s": 0.5, "curves": (0, 0)}]

print(functions._build_event_order(mock_crossings()))

# Oh wait, earlier my script had:
#        ordered.append([(e[2], e[3]) for e in evs])
# But then `ordered_events` would be a list of lists of events!
