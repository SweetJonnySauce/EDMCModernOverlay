# Design: Native GNOME Helper-Unavailable Legacy-Follow Fallback

**Status:** Proposed

## Context

The native GNOME Wayland bundle now enables fullscreen Shell-raster
presentation.  Its runtime currently derives missing-helper behavior from
`fullscreen_shell_raster_active`: an active profile returns a handled
`helper_unavailable` result.  Generic consumers convert that result into a
hidden-overlay cycle; `follow_surface` sees the cycle as handled and skips its
legacy follow controller.

That behavior is correct for the compatibility `gnome_shell_raster` identity,
which cannot safely present without the helper, but it changes the historical
native `gnome_shell_wayland` fallback.  The latter previously returned control
to the legacy follower when no helper presentation was available.  The full
test suite detects this through
`test_refresh_follow_geometry_uses_legacy_path_when_gnome_helper_is_not_available`.

## Goals

- Restore native GNOME's helper-unavailable legacy-follow fallback.
- Retain the compatibility raster bundle's fail-closed unavailable behavior.
- Keep this policy inside backend-owned GNOME runtime profiles.
- Preserve the fix219 boundary: no raw GNOME/raster enum dispatch or
  compositor-specific imports in generic consumers/follow code.
- Add deterministic regression evidence.

## Non-goals

- Changing fullscreen Shell-raster eligibility or its presentation lifecycle.
- Changing monitor placement, Mutter calls, DBus payloads, or helper protocol.
- Changing X11, xcompat, `load.py`, EDMC hooks, preferences, or plugin config.
- Removing the compatibility raster identity.

## Contract

The neutral presentation runtime profile gains a field whose semantic meaning
is independent of rendering mode, e.g. `helper_unavailable_is_terminal`.

| Profile | `fullscreen_shell_raster_active` | `helper_unavailable_is_terminal` | Missing-helper cycle outcome |
| --- | --- | --- | --- |
| Native GNOME Wayland | `True` | `False` | Return `None`; generic consumer yields no result and the follow surface runs legacy follow. |
| Legacy GNOME Shell Raster | `True` | `True` | Return `BackendPresentationRuntimeResult(helper_unavailable=True)`; generic consumer returns the existing hidden/fail-closed result. |

`fullscreen_shell_raster_active` continues to mean only “enable the existing
fullscreen Shell-raster route.”  It must not encode helper-loss ownership.

## Component interaction

```text
FollowSurface.refresh
  -> run_backend_presentation_cycle
       -> selected GNOME bundle runtime
            -> helper available: existing presentation runner
            -> helper unavailable + native profile: None
            -> helper unavailable + raster profile: unavailable result
  -> result is None: existing legacy follower refresh
  -> unavailable result: existing fail-closed hidden-overlay result
```

Generic `consumers.py` continues to translate only the neutral result type; it
does not decide which GNOME profile owns an unavailable helper.

## Failure handling and invariants

- Native helper loss is not treated as proof that legacy follow must be
  disabled; it falls through exactly once to the existing controller.
- Legacy raster helper loss remains terminal, does not invoke the presentation
  runner, and retains `presentation_state=helper_unavailable`.
- An available helper follows the existing native/raster presentation path
  unchanged.
- This change has no asynchronous work, UI-thread work, network I/O, payload
  schema, or lifecycle changes.

## Test strategy

Use unit tests: policy selection and its consequences are deterministic and
injected through backend status/runtime seams.  No `load.py` hook or EDMC
lifecycle wiring changes, so a harness test is not required.

Required evidence:

1. Follow-surface native helper-unavailable test calls legacy refresh once.
2. Native GNOME runtime without helper returns `None` and does not invoke the
   helper runner.
3. Legacy raster runtime without helper returns the existing unavailable
   result and does not invoke the runner.
4. Existing architecture-boundary tests show generic consumers and follow
   surface remain compositor-agnostic.
5. Existing eligible-fullscreen and windowed presentation tests stay green.

## Rollback

The change is limited to profile data and one unavailable-helper branch.  A
single revert restores the prior routing behavior.  No migration, persistent
setting, helper deployment, or protocol compatibility action is required.
