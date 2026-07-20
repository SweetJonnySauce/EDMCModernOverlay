# Step 01 Implementation and Test Plan

Test type: **unit tests**. All changed logic is pure/deterministic and no EDMC/plugin,
Tk/Qt, startup/shutdown, socket, or runtime lifecycle wiring is touched.

## Phase Tracking

| Phase | Status |
| --- | --- |
| Phase 1: Step 01 converged control plane | Completed |

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Verify state, read design/tasks, and map existing seams | Completed |
| 1.2 | Define complete acceptance coverage and implementation plan | Completed |
| 1.3 | Write all unit tests and capture expected RED failures | Completed |
| 1.4 | Implement models, codec, and shadow adapter to GREEN | Completed |
| 1.5 | Refactor and run targeted/project validation | Completed |
| 1.6 | Review and commit the completed Step 01 increment | Completed |

## Test Scenarios

1. **Enum and identity vocabulary**
   - Input: every design enum and stable/detected Linux instance.
   - Output: exact serialized values; `gnome_shell_raster` absent from converged identities.
2. **Immutable independent axes**
   - Input: supported + limited evidence + unavailable health.
   - Output: values remain independent; field, tuple, and nested-map mutation fails.
3. **Revision and age validation**
   - Input: zero/positive revisions and ages, then negative/bool values.
   - Output: valid records construct; invalid values raise `ValueError`/`TypeError` locally.
4. **Safe diagnostic boundaries**
   - Input: allowlisted primitives/nesting plus token, owner ID, handle, title, command,
     exception, and personal-path fixtures.
   - Output: accepted data is deeply immutable; prohibited content is absent and the
     constant redaction marker records that redaction occurred.
5. **Deterministic round trip**
   - Input: a complete envelope containing every top-level section.
   - Output: serialize/decode/serialize bytes match; decoded value is equivalent/immutable.
6. **Strict schema failure**
   - Input: missing, stale, future, boolean, and malformed schema versions/fields.
   - Output: explicit `incompatible_schema` or `malformed_envelope` result; no coercion.
7. **Bounded histories**
   - Input: more than the named failure/event limits.
   - Output: deterministic newest entries retained in construction and decoding.
8. **Privacy before formatting**
   - Input: adversarial nested diagnostics with sensitive keys and strings.
   - Output: serialized JSON never contains fixture secrets or personal data.
9. **Shadow identity/status fixtures**
   - Input: GNOME unavailable, native X11 healthy, XWayland degraded, and detected
     unimplemented Wayland statuses plus explicit evidence metadata.
   - Output: stable selected identities, independent support/evidence/health, normalized
     probes/helper summaries, and bounded safe failures.
10. **Shadow revisions and no-op path**
    - Input: disabled producer; equal snapshots; visible status change; attempted rollback.
    - Output: disabled returns `None`; equal retains revision; change increments; revisions
      never decrease.
11. **Transitional compatibility**
    - Input: representative existing `BackendSelectionStatus` before/after shadow adaptation.
    - Output: `to_payload()` output remains exactly equal and no production consumer changes.

## Implementation Sequence

1. Write all scenarios in the focused test module and the compatibility assertion first.
2. Run the targeted command and confirm imports/expected behavior fail (RED).
3. Add pure model records and boundary validation/freezing.
4. Add explicit codec encoders/decoders and history bounds.
5. Add the pure mapping table and injected shadow revision producer.
6. Run targeted tests after each implementation seam, refactor to repository conventions,
   then run lint, broader headless tests, `make check`, `make test`, and patch hygiene as
   available. GUI tests are not a required test type for this pure step.

## Validation Commands

- Requested targeted gate (expected unavailable in its stated environment):
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_status.py overlay_client/tests/test_backend_control_plane.py -q`
- Equivalent targeted gate:
  `.venv/bin/python -m pytest overlay_client/tests/test_backend_status.py overlay_client/tests/test_backend_control_plane.py -q`
- Focused lint:
  `.venv/bin/python -m ruff check overlay_client/backend/control_plane_models.py overlay_client/backend/control_plane_codec.py overlay_client/backend/shadow_status.py overlay_client/tests/test_backend_control_plane.py overlay_client/tests/test_backend_status.py`
- Headless suite: `.venv/bin/python -m pytest`
- Core check: `make check PYTHON=.venv/bin/python`
- Project test target: `make test PYTHON=.venv/bin/python`
- Patch hygiene: `git diff --check`

## Rollback and Compatibility

The increment is additive. Rollback removes the three new backend modules, focused tests,
exports, and code-assist notes. Existing production routing and transitional types remain the
behavioral oracle throughout.
