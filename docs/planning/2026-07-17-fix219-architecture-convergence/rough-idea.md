# Rough Idea: fix219 Architecture Convergence

Develop a detailed design and staged implementation plan for the work that remains after the existing `fix219` refactor and GNOME Wayland presentation Phase 19.

The project should distinguish formal validation/compliance/signoff from deeper architectural convergence. It should address evidence-based capability probing and selection, a single runtime composition root, behavior-owning backend contracts, GNOME behavior migration behind backend-owned bundles, distinct native Wayland strategies, backend-neutral lifecycle cleanup, stronger architecture and lifecycle tests, and staged decomposition of large GNOME modules.

The work must preserve existing behavior, particularly the Phase 19 atomic fullscreen monitor handoff, and follow a reversible contract-first, test-driven migration. Windows composition, portal fallback, Linux standalone behavior, capture policy, and geometry/follow redesign must remain explicitly scoped rather than being silently treated as complete.

Primary source context:

- `/tmp/handoff-20260717-135402.md`
- `docs/refactoring/fix219_cross_platform_overlay_architecture_research.md`
- `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md`
- `docs/refactoring/gnome_wayland_presentation_attachment.md`

