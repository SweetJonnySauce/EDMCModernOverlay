# Plan: Native GNOME Helper-Unavailable Fallback

## Acceptance-oriented test strategy

| Scenario | Input | Expected result |
| --- | --- | --- |
| Native profile helper absent | Selected native GNOME + unavailable helper + injected runner | `None`; zero runner calls; legacy follow refresh remains exactly once. |
| Legacy profile helper absent | Selected raster + unavailable helper + injected runner | Terminal unavailable result; zero runner calls; hidden diagnostics remain. |
| Profile separation | Both built bundles | Same active raster/fallback settings; native policy false, legacy policy true. |
| Boundary | Generic consumers and follow source | No compositor-specific imports or raw GNOME/raster dispatch. |

## Phases

| Phase | Description | Status |
| --- | --- | --- |
| 1 | RED unit regression coverage | Completed |
| 2 | GREEN profile-policy implementation | Completed |
| 3 | REFACTOR and focused validation | Completed with sandbox limitation |

### Phase 1

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add native direct unavailable-helper assertions | Completed |
| 1.2 | Extend legacy direct unavailable-helper assertions | Completed |
| 1.3 | Run focused RED command and record expected failures | Completed — three expected failures |

### Phase 2

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add neutral terminal-helper policy | Completed |
| 2.2 | Route missing-helper branch through policy | Completed |
| 2.3 | Set native false and legacy true | Completed |
| 2.4 | Run focused GREEN tests | Completed — 3 passed |

### Phase 3

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Review readability and fix219 boundary | Completed — no refactor needed |
| 3.2 | Run required focused pytest, Ruff, and diff check | Completed — 157 passed; Ruff and diff check passed |
| 3.3 | Run project check and separate sandbox-only failures | Completed with limitation — 1,649 passed, 21 skipped, 5 loopback socket setup errors |

## Implementation approach

Add one required dataclass field, set opposite explicit values in the two
GNOME profiles, and switch only the unavailable-helper branch to that field.
No generic consumer or follow-surface change is needed.
