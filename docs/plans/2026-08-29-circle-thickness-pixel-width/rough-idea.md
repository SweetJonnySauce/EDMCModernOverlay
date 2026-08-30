# Circle thickness should match legacy vectors

Change overlay circle payloads so `thickness=1` produces the same thin,
one-pixel logical Qt pen used by legacy vector outlines. Circle geometry still
scales with the legacy 1280×960 viewport; only its stroke-width policy changes.
Rectangle thickness semantics must remain unchanged.
