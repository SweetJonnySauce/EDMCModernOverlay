# Handoff: GNOME Content-Visibility Capability Contract

**Status:** Completed; no commit or staging performed.

**Files changed:** `overlay_client/backend/helper_ipc.py`,
`overlay_client/backend/__init__.py`, and
`overlay_client/tests/test_gnome_shell_helper_presentation_state.py`; task
context, plan, progress, and validation log under this directory.

**Validation commands/results:** RED collection failed as expected for the
missing capability export. GREEN/final:
`source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_backend_presentation_policy.py -q`
passed (134). Ruff on changed Python files and `git diff --check` passed.

**Decisions:** Kept the capability optional and GNOME-owned in `helper_ipc`;
capability negotiation emits a visibility wire field only for a healthy helper
that explicitly advertises it. Unsupported/malformed/legacy health resolves to
visible with no wire field. `allow_unfocused_target` remains untouched.

**Risks:** No extension capability advertisement, actor mutation, preference
wiring, or live GNOME test was performed; all are intentionally deferred to
later plan steps. The next helper step must implement and advertise the
contract before any supported live request can occur.

**Next exact action:** Main orchestration context should review this scoped
diff, record Task 02 on the execution dashboard, then close Step 1 and begin
the separately generated/code-assist-isolated Step 2 helper actor task.
