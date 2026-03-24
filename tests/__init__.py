"""
Test harness package for EDMC Neutron Dancer plugin.
"""

__all__ = ["TestHarness"]


def __getattr__(name: str):
    """Lazily import harness to avoid global side effects during pytest collection."""
    if name == "TestHarness":
        from harness import TestHarness

        return TestHarness
    raise AttributeError(name)
