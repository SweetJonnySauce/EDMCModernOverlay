# Step 3 Code-Assist Context

## Scope and prerequisites

- Task: `step03/task-01-deliver-helper-and-validate-live-gnome-wayland`.
- Prerequisites reconciled: `fa94da3c76a4136fe7f034e45fa2fbc9a7c0d9cd` (helper correction) and `fe35ac29ce96e1a17360fc1d298b1b657d730443` (diagnostic/readback evidence).
- This task adds no production or test behavior. It prepares evidence for a user-controlled GNOME Wayland acceptance gate.
- Excluded: X11, XWayland compatibility, renderer/payload work, generic follow/runtime code, backend selection, helper protocol/schema, settings, and presentation strategies.

## Existing documentation

`AGENTS.md` requires an explicit test-type decision, recorded validation, and a harness test only for `load.py`/lifecycle wiring. The orchestration prompt makes extension actions, session-bus probes, GNOME settings, EDMC, Elite, and live overlay control manual-only after a separate explicit approval.

The detailed design requires a valid monitor mismatch to move before resize, a matching applied rectangle before success, and preservation of fail-closed degradation. Step 2's retained regression evidence shows the boundary and retry/readback contracts are deterministic.

## Relevant paths and dependency map

```text
helpers/gnome_shell_extension/extension.js
  -> copied by scripts/dev_gnome_helper.sh update
  -> user-local helper UUID directory
  -> GNOME Shell helper/session bus
  -> manual Elite/overlay acceptance matrix

overlay_client/tests/test_gnome_* + test_backend_architecture_boundary.py
  -> deterministic pre-gate regression only
```

The delivery script clean-replaces only the dedicated user-local helper UUID
directory, requests extension enablement, and may require logout/login. It
honors its documented base override and Snap-aware home resolution. `status`
queries extension state/global user-extension state and calls the helper's
session-bus health method when available.

## Test-type decision

Selected: manual live GNOME Wayland integration/acceptance validation, preceded
by deterministic source-contract/unit regression. No harness test is needed:
this task changes neither `load.py` nor EDMC lifecycle/hook wiring, and adds no
code. The remaining risks—Mutter timing, monitor ownership, input, focus,
stacking, and resize—require a real user session.

## Current state

The deterministic pre-gate regression passed: 156 tests in 0.37s. The user
then personally completed the approved manual deployment/status gate: the
helper directory was clean-replaced; the session is GNOME Wayland
(`ubuntu:GNOME`); files are installed; the extension is enabled and ACTIVE;
DBus health is healthy; protocol is 3; and the `full_helper` feature gate has
presentation enabled. The live acceptance matrix remains pending.
