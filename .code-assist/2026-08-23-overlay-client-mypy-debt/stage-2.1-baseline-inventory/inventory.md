# Stage 2.1 Frozen Mypy Inventory

## Command result

Command: `source overlay_client/.venv/bin/activate && python -m mypy overlay_client`  
Exit status: `1`  
Raw combined output: `logs/mypy-overlay-client-baseline.raw.log`  
Mypy summary: `Found 203 errors in 27 files (checked 171 source files)`.

The raw log is the authoritative, unedited diagnostic record. The tables below
map every `error:` record by path and line to exactly one approved family. Mypy
`note:` lines are explanatory output, not errors, and are intentionally not
counted in the 203-error inventory.

## Shared-state — 81 errors

| Path | Error lines (one entry per error) | Count | Classification evidence |
| --- | --- | ---: | --- |
| `interaction_surface.py` | 20, 49, 91 | 3 | Indeterminate state read across mixin ownership. |
| `follow_surface.py` | 199, 208, 209, 372, 497, 882, 900, 933, 947, 959, 973, 974, 1077, 1156, 1157, 1168 | 16 | Follow and window state has incompatible or inferred ownership. |
| `control_surface.py` | 111, 119, 199, 209, 220, 227, 229, 246, 257, 273, 492, 494, 501, 503, 613, 718, 826, 843, 865, 874, 881, 883, 913, 1027, 1028, 1031, 1038, 1043, 1067, 1084 | 30 | Control state is initialized elsewhere and cannot be determined here. |
| `overlay_client.py` | 190 × 19 | 19 | `OverlayWindow` reports incompatible mixin state definitions and one indeterminate render field. |
| `tests/test_control_surface_platform_context.py` | 51 | 1 | Control-surface state stub optionality mismatch. |
| `tests/test_follow_surface_mixin.py` | 278, 279, 280, 284, 285, 288, 585, 739 | 8 | Follow-state stub and mutable mapping contract mismatch. |
| `tests/test_interaction_surface.py` | 37 | 1 | Interaction state stub optionality mismatch. |
| `tests/test_repaint_debounce.py` | 90, 100, 100 | 3 | Repaint/mixin method monkeypatch typing. |

## Pure-data — 34 errors

| Path | Error lines (one entry per error) | Count | Classification evidence |
| --- | --- | ---: | --- |
| `legacy_processor.py` | 240, 310, 312, 315, 318 | 5 | Mapping and legacy value container inference. |
| `follow_geometry.py` | 74, 76, 185, 187, 202, 204 | 6 | Integer-inferred geometry values receive floats. |
| `anchor_helpers.py` | 65, 66, 85, 86 | 4 | Anchor metadata dictionary accepts both float and string values. |
| `plugin_overrides.py` | 514, 523 | 2 | Prefix entry tuple shape conflicts with string tuple inference. |
| `payload_model.py` | 98 | 1 | Payload numeric coercion receives `object`. |
| `transform_helpers.py` | 203, 242 | 2 | Point tuple arity is inferred too broadly. |
| `tests/test_controller_target_box.py` | 555, 555, 556, 559, 561, 561, 564, 564, 565, 568, 568, 571, 650, 651 | 14 | Geometry/bounds helper stubs and method replacement signatures. |

## Renderer — 43 errors

| Path | Error lines (one entry per error) | Count | Classification evidence |
| --- | --- | ---: | --- |
| `vector_renderer.py` | 12 | 1 | Renderer protocol body lacks a return. |
| `debug_cycle_overlay.py` | 295, 296, 297, 556 | 4 | Renderer debug collections receive `object` and use invalid `any` type spelling. |
| `render_surface.py` | 168, 407, 964, 1124, 1235, 1569, 1578, 1629, 1647, 1701, 1704, 1708, 1712, 1717, 1721, 1914, 1934, 1962, 1964, 1966, 1970 | 21 | Render-state/cache, command-union, bounds, and measurement container types. |
| `tests/test_shell_raster_frame.py` | 378, 411, 412, 477, 480, 612, 613, 614, 648, 665, 681 | 11 | Shell-raster result fixtures access untyped objects. |
| `tests/test_render_surface_mixin.py` | 47, 56, 122, 352, 378, 439 | 6 | Render-surface stub attribute, override, and object-indexing contracts. |

## Integration — 45 errors

| Path | Error lines (one entry per error) | Count | Classification evidence |
| --- | --- | ---: | --- |
| `tests/test_backend_pressure_ab_runner.py` | 455, 481, 593, 754, 755 | 5 | Backend-runner boundary assertions and sample payload access. |
| `tests/test_backend_runtime_contracts.py` | 135, 136 | 2 | Combined backend presentation/input consumer stubs. |
| `tests/test_backend_status.py` | 421, 422, 433, 434 | 4 | Backend status payload access. |
| `tests/test_gnome_helper_presentation_runtime.py` | 360, 423, 457, 475, 801, 1563, 1577, 1819, 1831, 1872, 1886, 2025, 2182, 2197 | 14 | Helper/runtime callback captures and status payload access. |
| `tests/test_launcher_shell_raster_shutdown.py` | 11, 23, 36, 48, 60, 73 | 6 | Launcher shutdown callback return typing. |
| `tests/test_pressure_ab.py` | 326, 335, 344, 446, 461, 461, 542, 548, 611 | 9 | Pressure-AB integration document payload and immutable result assertions. |
| `tests/test_pressure_snapshot_window.py` | 76, 77, 78, 79, 80 | 5 | Pressure snapshot boundary payload access. |

## Taxonomy decision

No diagnostic establishes a fifth family. The directory-wide target is broader
than the earlier 115-error import-closure baseline: it includes 88 additional
errors in existing tests and integration-adjacent surfaces. Those errors still
fall within the approved shared-state, pure-data, renderer, and integration
families; they are preserved as inventory, not suppressed. Coordinator review is
required before opening the next isolated stage, and no scope expansion occurs in
this context.
