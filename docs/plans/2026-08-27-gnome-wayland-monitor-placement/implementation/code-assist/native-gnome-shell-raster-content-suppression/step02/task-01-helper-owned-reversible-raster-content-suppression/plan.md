# Plan: Helper-Owned Reversible Raster Content Suppression

## Test strategy

| Scenario | Expected result |
| --- | --- |
| Helper health capability | The extension advertises `shell_raster_content_visibility`. |
| Supported update | The normalized request reaches one content-only helper method after a normal raster update. |
| Single-frame cycle | The existing record receives opacity zero then 255; no actor lifecycle API is used. |
| Region cycle | Every existing region record receives the same content-only operation. |
| Malformed/mutation failure | Effective state is visible with a diagnosable degraded result. |
| Hard lifecycle loss | Existing clear/suspend paths remain outside the content-only method. |

## Implementation

1. Add the capability to the extension's full-helper capability list.
2. Normalize the optional request into a small helper-owned descriptor.
3. Apply opacity and record-local state to retained single and region records;
   restore opacity to visible if mutation fails.
4. Include requested/effective/support/applied/degraded fields in the existing
   Shell-raster result payload, without changing ordinary lifecycle paths.
5. Run the focused source/contract pytest selection, `gjs --check`, and the
   scoped diff check.

## TDD record

- [x] RED source/contract tests added and observed failing.
- [x] GREEN helper capability and mutation implementation added.
- [x] REFACTOR review and focused validation completed.
