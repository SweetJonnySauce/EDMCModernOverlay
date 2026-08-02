"""Cheap fixed-cardinality counters for runtime work attribution."""

from __future__ import annotations

from typing import MutableMapping

WORK_COUNTER_MAX = 1_000_000


def increment_bounded_counter(
    counts: MutableMapping[str, int],
    key: str,
    *,
    limit: int = WORK_COUNTER_MAX,
) -> None:
    """Increment an existing counter without growing keys or exceeding ``limit``."""

    if key not in counts:
        return
    current = max(0, int(counts.get(key, 0)))
    counts[key] = min(max(0, int(limit)), current + 1)
