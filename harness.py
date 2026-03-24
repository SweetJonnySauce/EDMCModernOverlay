"""Stable local test-harness entrypoint."""

from __future__ import annotations

from tests.harness_bootstrap import get_test_harness_class


TestHarness = get_test_harness_class()

__all__ = ["TestHarness"]
