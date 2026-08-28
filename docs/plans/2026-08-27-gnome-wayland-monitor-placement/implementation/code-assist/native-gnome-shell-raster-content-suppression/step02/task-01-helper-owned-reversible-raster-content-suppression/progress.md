# Progress: Helper-Owned Reversible Raster Content Suppression

## Checklist

- [x] Setup and source-pattern exploration completed.
- [x] RED tests added and verified.
- [x] GREEN implementation completed.
- [x] REFACTOR review and validation completed.

## Decisions

- Use `Clutter.Actor.set_opacity(0|255)` as the reversible content-only
  mechanism. It preserves the actor object and attachment, unlike `hide`.
- Treat malformed requests or mutation errors as degraded stable-visible
  outcomes. No ordinary-focus path may invoke cleanup.
- Source contracts plus `gjs --check` are the available helper-side evidence;
  live GNOME behavior remains expressly deferred.

## TDD evidence

### RED

Added two focused extension-source tests. Before implementation:

```text
python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py -k 'reversible_raster_content_visibility or raster_content_visibility_method' -q
2 failed
```

The expected failures showed the missing helper capability and missing
content-only operation.

### GREEN

Added the helper capability plus a normalized request and `set_opacity(0|255)`
operation over `_shellRasterActorRecords(targetToken)`. The method has no
clear/suspend/hide/remove/destroy/show calls, restores visible opacity after a
mutation failure, and records only content visibility on the retained records.

### REFACTOR and validation

Reviewed the focused diff against the lifecycle helpers. The operation is
separate from hard cleanup and does not alter `allow_unfocused_target`.

```text
python -m ruff check overlay_client/tests/test_gnome_shell_helper_extension_source.py
All checks passed

python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py -q
162 passed

git diff --check
passed
```

The installed `gjs` does not implement `--check`, and no independent JavaScript
syntax checker is installed. The Python extension-source contract suite passed;
live GNOME and D-Bus verification remain deferred by orchestration policy.
