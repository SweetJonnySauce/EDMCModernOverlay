# Step 01 Code Context

## Scope

Implement the three approved Step 01 code tasks:

1. immutable converged backend/control-plane models;
2. deterministic schema-version-1 serialization and strict decoding;
3. a developer-only shadow adapter from `BackendSelectionStatus`.

Production selection, `BackendSelectionStatus.to_payload()`, content/settings payloads,
bundle resolution, presentation behavior, and Phase 19 behavior remain unchanged.

## Existing Documentation

- `AGENTS.md`: requires plan-first implementation, pure-helper unit tests, behavior-preserving
  backend boundaries, exact test evidence, and numbered phase/stage tracking.
- `README.md`: identifies this as the Python EDMC Modern Overlay plugin and client.
- `docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md`:
  defines stable identities, exact enum values, three independent status axes, immutable
  schema-v1 snapshots, bounded histories, privacy exclusions, and shadow-only migration.
- `docs/planning/2026-07-17-fix219-architecture-convergence/implementation/plan.md`:
  makes Step 01 additive and requires focused unit tests plus `git diff --check`.
- `.agents/tasks/2026-07-17-fix219-architecture-convergence/step01/`: contains the three
  task specifications and acceptance criteria. The entire `.agents` tree is pre-existing,
  untracked user work and will not be modified.

No `CODEASSIST.md` exists. Project-specific constraints are supplied by `AGENTS.md`; a
separate `CODEASSIST.md` could be added later if the team wants reusable SOP overrides.

## Existing Structure and Patterns

- Transitional types live in `overlay_client/backend/contracts.py` and
  `overlay_client/backend/status.py` and are re-exported from `overlay_client/backend/__init__.py`.
- Existing status regression tests live in `overlay_client/tests/test_backend_status.py`.
- New focused coverage belongs in `overlay_client/tests/test_backend_control_plane.py`.
- Python baseline for client code is 3.10+, with frozen/slotted dataclasses and string enums
  already used in backend modules.
- Deterministic JSON elsewhere uses sorted keys and compact separators.
- Developer mode is process-start gated through `version.is_dev_build`/
  `MODERN_OVERLAY_DEV_MODE`; the new shadow producer will accept an injected enabled flag so
  its release path returns before adaptation or serialization work.

## Requirements and Acceptance Mapping

- Preserve the design's exact probe/support/evidence/health/outcome/recovery values.
- Preserve stable Linux identities and normalize transitional GNOME raster to the one shadow
  `gnome_shell_wayland` identity; do not expose raster as a converged production identity.
- Validate non-negative revisions/ages locally without cross-process clock comparison.
- Deep-copy and freeze diagnostic mappings and decoded collections.
- Allowlist diagnostics at their owning boundaries; redact secrets, identifiers, handles,
  titles, commands, exceptions, and personal paths before JSON formatting.
- Retain deterministic newest entries when failure/event histories exceed named bounds.
- Return explicit decode failures for incompatible versions and malformed payloads.
- Keep support policy, evidence, and health independently supplied/derived; evidence is an
  explicit shadow-adapter input and never inferred from health or compositor labels.
- Keep capture exclusion as a capability ID only.
- Retain revisions for equivalent shadow snapshots and increment only on visible changes.

## Dependency Map

```text
transitional BackendSelectionStatus
        + explicit producer/support/evidence metadata
        -> shadow_status adapter (diagnostic only)
        -> immutable control_plane_models
        -> control_plane_codec
        -> deterministic comparison JSON

existing selector/bundles/status payloads/presentation
        -> unchanged production path
```

## Implementation Paths

- `overlay_client/backend/control_plane_models.py`: pure enums, immutable records,
  validation, immutable JSON-safe diagnostic boundaries.
- `overlay_client/backend/control_plane_codec.py`: explicit schema-v1 primitive mapping,
  deterministic JSON, strict decoder, normalized decode result.
- `overlay_client/backend/shadow_status.py`: pure transitional mapping and injected
  developer-only monotonic revision producer.
- `overlay_client/backend/__init__.py`: minimal public exports only.
- `overlay_client/tests/test_backend_control_plane.py`: models, codec, privacy, histories,
  shadow fixtures, and revision behavior.
- `overlay_client/tests/test_backend_status.py`: one byte-for-byte transitional-payload guard.

## Environment and Risks

- `overlay_client/.venv/bin/python` exists but has no pytest or ruff.
- Root `.venv/bin/python` has pytest 8.3.3, ruff 0.3.7, and mypy 1.10.0 and will be used.
- The schema's nested summary fields are conceptual in the design. The implementation will
  use explicit, narrow records and strict field sets while retaining the exact top-level
  shape and semantics.
- No manual GUI or compositor validation is required because Step 01 changes no behavior.
