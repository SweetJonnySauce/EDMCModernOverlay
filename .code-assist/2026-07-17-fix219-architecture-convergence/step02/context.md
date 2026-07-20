# Step 02 Code Context

## Scope

Implement the three approved Step 02 code tasks:

1. behavior-oriented runtime, discovery, presentation, input-policy, and optional helper
   lifecycle contracts;
2. generic unavailable and unimplemented runtimes that fail closed;
3. a deterministic paper backend and reusable backend-runtime contract suite under test
   support only.

Production selection, bundle construction, launcher ownership, backend registration,
presentation, input, discovery, content/settings payloads, and Phase 19 behavior remain
unchanged.

## Existing Documentation

- `AGENTS.md`: requires plan-first implementation, explicit test selection, pure-service unit
  tests, behavior-preserving backend boundaries, exact validation evidence, and numbered
  phase/stage tracking.
- `README.md`: identifies the repository as the Python EDMC Modern Overlay plugin/client.
- `docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md`:
  defines the process-lifetime runtime, separate behavioral services, normalized intents and
  results, lifecycle invariants, three independent status axes, privacy boundaries, and the
  paper-backend extension point.
- `docs/planning/2026-07-17-fix219-architecture-convergence/implementation/plan.md`:
  makes Step 02 additive, keeps transitional assertions, and requires the focused contract
  gate plus a deterministic lifecycle demo.
- `.agents/tasks/2026-07-17-fix219-architecture-convergence/step02/`: contains the three
  approved task specifications and acceptance criteria.
- Step 01 records under the sibling `step01/` directory establish the existing model/codec
  conventions and the root `.venv` as the canonical developer/test environment.

No `CODEASSIST.md` exists. Project-specific constraints are supplied by `AGENTS.md` and the
approved fix219 documents.

## Existing Structure and Patterns

- Transitional nominal/factory contracts remain in `overlay_client/backend/contracts.py` and
  are re-exported by `overlay_client/backend/__init__.py`.
- Step 01 immutable status vocabulary, privacy sanitization, and schema-v1 records live in
  `control_plane_models.py`; deterministic serialization lives in
  `control_plane_codec.py`.
- Existing transitional assertions live in
  `overlay_client/tests/test_backend_contracts.py` and must remain intact, including the
  temporary combined presentation/input adapter assertion.
- New behavioral contract coverage belongs in
  `overlay_client/tests/test_backend_runtime_contracts.py`.
- Paper-backend and reusable-suite implementations belong under test support and must not be
  imported by production selectors, bundles, launchers, package exports, or consumers.
- Python 3.10 compatibility, frozen/slotted dataclasses, runtime-checkable protocols, string
  enums, and explicit validation are established backend conventions.

## Requirements and Acceptance Mapping

- Runtime identity is immutable, service access is stable, start is attempted once, stop is
  safe in every lifecycle state and idempotent, partial starts clean up in reverse ownership
  order, and stopped runtimes cannot resume.
- Discovery owns normalized target appearance/loss snapshots; presentation owns visible and
  hidden state; input owns click-through/focus state; helper lifecycle is optional and visible
  to generic status only through a normalized health snapshot.
- Presentation and input protocols remain separately revisioned. Independent objects and one
  combined implementation must both structurally conform; no test may require identity.
- Presentation intent expresses only windowed, borderless-fullscreen, or hidden behavior plus
  normalized geometry, coordinate-space, revision, visibility, frame, and interaction data.
- Generic contracts contain no Qt/Tk types, concrete factories, GNOME renderer/action/D-Bus
  terms, helper tokens, Overview actions, or private target handles.
- Unavailable runtimes preserve a selected identity and independently supplied support and
  evidence while reporting unavailable/incompatible live health and explicit recovery.
- Unimplemented runtimes report unimplemented support, unavailable health, terminal recovery,
  never construct a fallback, and keep all presentation hidden.
- Cleanup continues after injected individual failures, respects the deterministic injected
  deadline between owned resources, bounds retained failures, and sanitizes diagnostics before
  schema-v1 serialization.
- The paper backend covers deterministic target appearance/loss/recovery, present/pending/hide/
  unavailable outcomes, independent input changes, owner loss, partial-start cleanup, repeated
  stop, monotonic revisions, and schema-v1 round trips.

## Dependency Map

```text
Step 01 identity/status/result/schema models
        -> runtime contract models and runtime-checkable behavioral protocols
        -> generic unavailable/unimplemented inert services and runtimes
        -> schema-v1 runtime status snapshots

test-only backend runtime factory protocol
        -> reusable observable contract assertions
        -> deterministic paper runtime and injected controls
        -> Step 02 lifecycle demo

existing selector/bundles/launcher/consumers/load.py
        -> unchanged transitional production path
```

## Implementation Paths

- `overlay_client/backend/runtime_contracts.py`: pure normalized enums/records, opaque surface
  and target-observer boundaries, service protocols, and the process-lifetime runtime protocol.
- `overlay_client/backend/failure_runtimes.py`: stable inert services plus directly
  constructible unavailable and unimplemented runtimes with normalized schema-v1 status.
- `overlay_client/backend/__init__.py`: public exports for production-ready generic contracts
  and failure runtimes only.
- `overlay_client/tests/backend_runtime_testkit.py`: test-only factory protocol, deterministic
  controls/resources, paper backend, and reusable observable contract assertions.
- `overlay_client/tests/test_backend_runtime_contracts.py`: acceptance surface for contracts,
  failure runtimes, schema/privacy behavior, paper lifecycle, and production isolation.
- `overlay_client/tests/test_backend_contracts.py`: retained transitional tests; add only a
  focused independent/combined structural-conformance assertion if needed.

## Environment and Risks

- Root `.venv/bin/python` supplies pytest, ruff, and mypy; `overlay_client/.venv` remains a
  runtime environment and is not used for tests.
- This step models cleanup deadlines with an injected monotonic clock and checks the deadline
  between deterministic resource releases. It does not introduce worker threads or claim to
  preempt an arbitrarily blocking third-party callback.
- Runtime status assembly must reuse Step 01 sanitization and codec rather than inventing a
  second serializer.
- Runtime protocol conformance is structural; behavioral lifecycle guarantees are proved by
  the reusable suite.
- No manual GUI or compositor validation is required because no production behavior or wiring
  changes in Step 02.
