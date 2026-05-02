"""
Test harness package for EDMC Neutron Dancer plugin.
"""

__all__ = ["TestHarness"]


def __getattr__(name: str):
    """Lazily resolve TestHarness to avoid global side effects during pytest collection."""
    if name == "TestHarness":
        from .harness_bootstrap import get_test_harness_class

        return get_test_harness_class()
    raise AttributeError(name)
