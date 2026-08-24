# Task: Freeze Directory-Wide Overlay-Client Mypy Baseline

## Description

Run the approved directory-wide overlay-client mypy baseline once, preserve its exact output in
this stage directory, and classify every reported error into the four approved families:
shared-state, pure-data, renderer, or integration. This stage establishes the RED inventory only;
it must not alter source, tests, mypy configuration, or the baseline to make it smaller.

## Background

The approved parent plan identifies 115 import-closure errors from the prior
`overlay_client/overlay_client.py` baseline and requires the directory-wide command as the
enforced target. The separate native-X11 transparent-surface-clear repair is intentionally dirty
and must remain intact. The user approved the parent plan and orchestration prompt; that approval
also approves this single-task breakdown, so no new decision is required.

## Reference Documentation

**Required:**
- Design: `.code-assist/2026-08-23-overlay-client-mypy-debt/plan.md`
- Context: `.code-assist/2026-08-23-overlay-client-mypy-debt/context.md`
- Orchestration: `.code-assist/2026-08-23-overlay-client-mypy-debt/orchestration-prompt.md`
- Prior repair boundary: `.code-assist/2026-08-21-fix219-x11-surface-artifacts/`

**Note:** Read the governing artifacts, current dashboard, this task, and the immediately
preceding handoff before implementation. Treat the parent-plan approval as task-breakdown
approval.

## Technical Requirements

1. Before the command, inspect `git status --short`, the scoped diff, the dashboard, and all
   existing Stage 2.1 artifacts; preserve unrelated dirty work unchanged.
2. Run exactly `source overlay_client/.venv/bin/activate && python -m mypy overlay_client` once
   and save unedited stdout/stderr plus exit status in this stage directory.
3. Produce a concise inventory mapping each reported file/error to exactly one approved family:
   shared-state, pure-data, renderer, or integration. Record any genuinely new family separately
   and stop for plan review rather than widening scope or adding suppressions.
4. Do not edit production, test, configuration, or top-level progress/dashboard files. Do not run
   unrelated validation. Do not use blanket ignores, broad `Any`, or type suppressions.
5. Leave a handoff with exactly these fields: `Status; Files changed; Validation
   commands/results; Decisions; Risks; Next exact action.`

## Dependencies

- Existing `overlay_client/.venv` with mypy installed.
- The approved mypy-debt plan and orchestration prompt.
- The preserved fix219/X11 worktree and records.

## Implementation Approach

1. Reconcile the stage state and freeze the command output without modifying the worktree.
2. Classify the frozen output against the parent-plan taxonomy and identify the first family for
   Stage 2.2 without proposing a code repair.
3. Record the exact result, scope decision, and handoff in this stage directory for coordinator
   review.

## Acceptance Criteria

1. **Reproducible RED baseline**
   - Given the existing client virtual environment and unchanged worktree
   - When `python -m mypy overlay_client` runs once
   - Then the raw output and exit status are preserved in this stage directory without source or
     configuration edits.

2. **Complete bounded classification**
   - Given the frozen mypy output
   - When each error is inventoried
   - Then every error is assigned to shared-state, pure-data, renderer, or integration, and any
     new family is explicitly marked for plan review.

3. **X11 and fix219 preservation**
   - Given the intentionally dirty independent repair
   - When Stage 2.1 completes
   - Then no production, test, configuration, top-level progress, or dashboard file has changed
     and no compositor-specific policy has entered generic paths.

4. **Stage-local evidence**
   - Given the completed inventory
   - When the coordinator reviews Stage 2.1
   - Then the stage directory contains the raw command evidence, classification, and an exact
     six-field handoff.

## Metadata

- **Complexity**: Low
- **Labels**: mypy, baseline, inventory, type-safety, stage-2.1
- **Required Skills**: Python typing, mypy diagnosis, scoped worktree review

