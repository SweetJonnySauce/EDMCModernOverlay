# Plan: GNOME Content-Visibility Capability Contract

## Test strategy

| Scenario | Input | Expected result |
| --- | --- | --- |
| Supported suppression | Healthy helper advertises the optional capability; requested `suppressed` | Wire request contains `content_visibility=suppressed`; signature differs; continuity flag remains true. |
| Default/legacy visible request | No optional visibility field | Existing wire payload and signature remain unchanged. |
| Capability missing | Healthy baseline helper lacks optional capability; requested `suppressed` | Negotiation emits no visibility field, reports effective `visible` and a machine-readable unsupported reason. |
| Malformed/unsafe health | Unhealthy or malformed health status; requested `suppressed` | Same stable-visible no-op result. |
| Result parsing | Helper reports valid, invalid, or unsupported visibility result | Valid supported value is represented; invalid/unsupported is never treated as successful suppression. |

## Implementation checklist

- [x] Explore the helper IPC, health validation, raster request, and status seams.
- [x] RED: Add contract tests for negotiation, optional serialization, signatures, and parsed results.
- [x] GREEN: Add native-GNOME capability types, capability negotiation, and fail-closed parsing.
- [x] REFACTOR: Export only the necessary backend contracts and align names with existing models.
- [x] Validate focused tests, Ruff, and diff whitespace.

## Risk control

The new capability is optional rather than baseline-required. Consequently,
the currently installed helper receives no new field and preserves its existing
visible actor behavior. Preference wiring and extension changes are explicitly
out of scope.

## Completed implementation

- Added optional `shell_raster_content_visibility` capability negotiation in
  the GNOME helper IPC module. It resolves every unhealthy or
  capability-missing response to visible with no wire field.
- Added typed optional raster request/status values. A supported value changes
  the raster request signature; a no-op value remains omitted from the
  payload.
- Parsed helper result values fail closed to a presentation degrade reason when
  malformed, unsupported, or absent after a requested visibility operation.
