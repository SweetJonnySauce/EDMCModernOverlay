# Stage 3.1 Context — Pure Data Types

## Bounded scope

This fresh implementation context owns only the frozen pure-data diagnostics in
`follow_geometry.py`, `anchor_helpers.py`, `legacy_processor.py`,
`plugin_overrides.py`, `payload_model.py`, and `transform_helpers.py`. It may
make source-proven annotation/container-shape corrections only. It must not
change runtime calculations, filtering, serialization, payload acceptance,
TTL expiry, Qt lifecycle, MRO, follow behavior, renderer behavior, config,
`load.py`, or the independent fix219 X11 surface repair.

## Evidence and dependency map

Stage 2.1's frozen 203-error directory-wide baseline assigns the listed source
diagnostics to the pure-data family. Stage 2.3 completed the shared-state
family; its focused target retains only renderer diagnostics reserved for
Stage 3.2. The expected source contracts are: float native-origin
intermediates ending in integer geometry; trace details containing floats and
strings; heterogeneous legacy point mappings; `PrefixEntry` tuples; and exact
two-float transformed points.

`PayloadModel.ingest` is a stop edge. The payload surface is `dict[str,
object]`, while the existing implementation passes the TTL directly to
`int()`. This context will inspect producers and call sites for a precise,
type-only representation. If they cannot prove the complete accepted coercion
contract, the diagnostic remains and the handoff will request coordinator
review; no guard, cast, ignore, or behavior change is allowed.

## Test selection

Static mypy RED/GREEN is the primary proof because all planned corrections are
annotation-only. The required focused pure-unit slice guards the existing
geometry, anchor, transform, payload/dedupe, and override behavior. No test
file is planned: no runtime behavior changes are authorized. No harness test
applies because `load.py` and EDMC lifecycle wiring are out of scope.

## Boundary and worktree controls

The dirty fix219 worktree is user work and remains untouched. Generic client
paths must remain compositor-neutral; this pure-data work adds no backend or
compositor imports and no raw backend/helper enum dispatch. The clear-first
transparent-surface behavior remains outside the six-module source scope.

## Result and stop evidence

The sole RED/GREEN pair improved the focused result from 16 to 5 errors. The
source-proven anchor and legacy corrections cleared their diagnostics, as did
the standard geometry conversion. Four clamp-conversion errors remain because
the function's earlier integer-valued branch assignments establish the local
type before the later annotated assignments; remediation must declare the
shared local at that earlier seam. The TTL diagnostic remains intentionally
unresolved: the decoded object payload boundary and reachable call sites do not
prove a closed type that represents every existing direct `int()` coercion.
No runtime guard, coercion, cast, or input restriction was added.
