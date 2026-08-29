# Step 1 / Task 1 context

## Scope

Add only the normal-circle regression test in
`overlay_client/tests/test_payload_bounds.py`. Production code is intentionally
unchanged in this task.

## Contract

For a circle with centre `(100, 200)` and radius `25`, Fill-mode group bounds
must cover `(75, 175)` through `(125, 225)`.

## Dependency map

`LegacyItem` → `payload_transform.accumulate_group_bounds()` → `GroupBounds`.
The helper currently routes circles through the generic centre-point fallback,
so the test is intentionally red until Step 2 adds circle-specific bounds.

## Test selection

This is a deterministic pure-helper unit test. It does not require an EDMC
lifecycle, socket, renderer, or BioScan integration harness.
