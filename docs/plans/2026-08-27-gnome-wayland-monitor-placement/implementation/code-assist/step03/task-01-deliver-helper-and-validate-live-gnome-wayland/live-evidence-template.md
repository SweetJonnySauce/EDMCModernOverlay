# Step 3 Live Acceptance Evidence

Provide only non-secret values. For every row, include: target monitor index;
overlay pre/post monitor index; action label; requested rectangle; applied
rectangle; degrade reasons; bounded-retry result; and observed result. A visual
success with a non-matching applied rectangle is **FAIL**.

| Case | Result (PASS/FAIL) | Required evidence and observation |
| --- | --- | --- |
| 1. Elite primary, overlay initially secondary | Pending | Transfer ends on primary; guarded transfer action; requested/applied rectangles match. |
| 2. Elite secondary, overlay initially primary | Pending | Transfer ends on secondary; guarded transfer action; requested/applied rectangles match. |
| 3. Repeated cross-monitor moves | Pending | No accumulated offset; bounded retry only if readback lags. |
| 4. Already co-located | Pending | No unnecessary transfer action; requested/applied rectangles match. |
| 5. Click-through, focus, stacking, and resize | Pending | Overlay remains click-through, does not steal focus, stays above Elite, follows resize, and has no chrome regression; matching readback required. |

If any row fails, include only its non-secret diagnostics and stop for direction;
do not add sleeps, coordinate guesses, fullscreen workarounds, or cross-backend
fallbacks.
