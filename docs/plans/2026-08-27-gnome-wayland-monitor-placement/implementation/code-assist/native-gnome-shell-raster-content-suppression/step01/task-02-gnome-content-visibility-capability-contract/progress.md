# Progress: GNOME Content-Visibility Capability Contract

## Checklist

- [x] Setup and instruction discovery
- [x] Explore requirements and existing patterns
- [x] Plan unit/contract tests
- [x] RED test run
- [x] GREEN implementation and test run
- [x] Refactor/review
- [x] Final focused validation

## Setup notes

Auto mode is active. The task directory and `logs/` exist. `CODEASSIST.md` was
not found in the repository discovery; repository `AGENTS.md`, the task,
design, lessons, and relevant backend/test files were read.

## TDD record

### RED

Added pure contract tests before implementation. The focused state test failed
during collection because the optional capability export did not yet exist:
`ImportError: cannot import name
'GNOME_SHELL_HELPER_CAPABILITY_RASTER_CONTENT_VISIBILITY'`.

### GREEN

Added a native-GNOME optional capability identifier, typed visibility request
and result values, capability negotiation, optional request serialization and
signature material, and fail-closed presentation-result parsing. The optional
capability is intentionally excluded from baseline required capabilities, so
the installed/older helper follows the pre-existing visible request path.

### Refactor and review

Kept generic `presentation_policy.py` untouched. The protocol-specific types
and capability check remain in `helper_ipc.py`, exported through the backend
contract package. No preference wiring, actor mutation, protocol version bump,
or `allow_unfocused_target` behavior changed.

## Test evidence

| Command | Result |
| --- | --- |
| `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_shell_helper_presentation_state.py -q` | RED: expected missing-export collection failure; GREEN: 30 passed. |
| `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_backend_presentation_policy.py -q` | 134 passed. |
| `source overlay_client/.venv/bin/activate && python -m ruff check overlay_client/backend/helper_ipc.py overlay_client/backend/__init__.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py` | Passed. |
| `git diff --check` | Passed. |

No live GNOME/D-Bus validation was run: this task adds no extension behavior
and the orchestration explicitly defers live validation.
