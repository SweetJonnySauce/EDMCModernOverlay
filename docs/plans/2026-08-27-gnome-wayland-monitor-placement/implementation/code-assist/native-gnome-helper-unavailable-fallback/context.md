# Context: Native GNOME Helper-Unavailable Fallback

## Scope

Restore native `gnome_shell_wayland` helper-loss fall-through while retaining
terminal, fail-closed helper-loss behavior for `gnome_shell_raster`. Production
scope is restricted to `overlay_client/backend/presentation_runtime.py` and
`overlay_client/backend/bundles/gnome_shell_wayland.py`.

## Requirements and unchanged behavior

- Add neutral `helper_unavailable_is_terminal` profile policy; it is separate
  from `fullscreen_shell_raster_active`.
- Native GNOME missing helper returns `None`; its injected runner is not called.
- Legacy raster missing helper returns `helper_unavailable`; its runner is not
  called and generic consumer diagnostics remain fail-closed.
- Preserve active fullscreen Shell-raster and managed-PyQt fallback-suppression
  flags for both profiles.
- Preserve fix219: generic consumer and follow code remain compositor-agnostic.
- No `load.py`, lifecycle, UI, helper protocol, settings, or EDMC work changes.

## Test selection

Unit tests are required: bundle profile selection and injected runner behavior
are deterministic. A harness test is not required because no `load.py`, EDMC
hook, startup/shutdown, or lifecycle wiring changes.

## Dependency map

`GnomeShellPresentationRuntime` consumes the neutral profile and returns a
neutral result. `run_backend_presentation_cycle` translates that result without
GNOME enum dispatch. `follow_surface` invokes the existing legacy follower only
when no cycle result is returned.

## Existing documentation

Read: approved remediation design, implementation plan, remediation plan,
orchestration prompt, fullscreen routing plan/dashboard, iteration checklist,
`AGENTS.md`, and the focused test/runtime source. No `CODEASSIST.md` exists;
the repository's `AGENTS.md` and approved task provide the governing rules.

## Worktree safety

The pre-existing dirty paths recorded by the remediation dashboard remain
user-owned. This task creates only this isolated documentation directory,
scoped tests, the two approved production files, and its handoff.
