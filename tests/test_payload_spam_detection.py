from __future__ import annotations

from overlay_plugin import spam_detection


def test_payload_spam_tracker_warns_and_throttles() -> None:
    warnings: list[str] = []

    def _warn(msg: str, *args) -> None:
        warnings.append(msg % args if args else msg)

    tracker = spam_detection.PayloadSpamTracker(_warn)
    tracker.configure(
        spam_detection.SpamConfig(
            enabled=True,
            window_seconds=1.0,
            max_payloads=3,
            warn_cooldown_seconds=5.0,
            exclude_plugins=(),
        )
    )

    base = 100.0
    for idx in range(4):
        tracker.record("Spammy", now=base + idx * 0.1)
    assert len(warnings) == 1

    tracker.record("Spammy", now=base + 0.6)
    tracker.record("Spammy", now=base + 0.7)
    assert len(warnings) == 1

    later = base + 6.0
    for idx in range(4):
        tracker.record("Spammy", now=later + idx * 0.1)
    assert len(warnings) == 2


def test_payload_spam_tracker_excludes_plugin() -> None:
    warnings: list[str] = []

    def _warn(msg: str, *args) -> None:
        warnings.append(msg % args if args else msg)

    tracker = spam_detection.PayloadSpamTracker(_warn)
    tracker.configure(
        spam_detection.SpamConfig(
            enabled=True,
            window_seconds=1.0,
            max_payloads=1,
            warn_cooldown_seconds=0.0,
            exclude_plugins=("spammy",),
        )
    )

    tracker.record("Spammy", now=200.0)
    tracker.record("Spammy", now=200.1)
    assert warnings == []
