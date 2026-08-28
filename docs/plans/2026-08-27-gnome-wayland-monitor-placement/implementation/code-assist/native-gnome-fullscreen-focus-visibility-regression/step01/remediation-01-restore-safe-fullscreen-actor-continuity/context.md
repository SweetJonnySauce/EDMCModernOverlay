# Remediation 01 Context

**Date:** 2026-08-28

## Scope

Restore only the pre-`8ef91cd` native GNOME fullscreen Shell-raster actor
continuity path after the user reported a black screen when focus returned to
Elite. Planning/orchestration evidence and all unrelated work remain intact.

## Test selection

Unit tests are required and sufficient. The behavior is deterministic
backend-bundle authorization with injected helper input; it does not touch
`load.py` or EDMC lifecycle wiring.

## Safety contract

An eligible full-monitor fullscreen Shell-raster target must keep
`allow_unfocused_target=True` across an ordinary unfocused interval so the
compositor-owned actor is not transiently suspended. This rollback does not
claim that the unchecked preference is now honored; safe content-only
suppression needs a separately approved renderer-level design.
