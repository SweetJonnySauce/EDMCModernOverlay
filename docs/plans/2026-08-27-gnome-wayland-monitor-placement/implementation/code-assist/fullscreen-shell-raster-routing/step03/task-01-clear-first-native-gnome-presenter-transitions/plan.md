# Plan: Clear First Native GNOME Presenter Transitions

## Test strategy

| Scenario | Input / expected output |
| --- | --- |
| Stable raster to windowed | Recording callbacks produce `clear`, then `prepare`, then managed `attach`; clear is acknowledged. |
| Clear failure | Recording clear raises; no preparation or managed attach occurs and the result is suppressed/degraded. |
| Existing loss/replacement contracts | Target replacement and helper loss retain `HIDE_ALL`/cache reset behavior with clear where contact is safe. |
| Existing fullscreen failure contracts | No provider/frame success remains clear/suppressed, never a managed fullscreen attach. |

## Implementation

1. Add the recording-order unit contract first and run it to demonstrate the
   pre-repair order failure.
2. Gate the guarded managed commit on acknowledged clear before calculating or
   applying the managed surface preparation or issuing its attach request.
3. Run the focused Step 3 suite, inspect/refactor only for surrounding style,
   then run diff and secret review.

## Risks and controls

The guarded branch must not accidentally discard its grace/sample state. The
smallest control is to preserve the existing decision engine and only relocate
the clear gate. No timers, coordinate logic, fallback presenter, or public
protocol changes are permitted.
