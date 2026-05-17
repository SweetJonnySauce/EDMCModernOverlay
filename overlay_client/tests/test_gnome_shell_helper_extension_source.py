from __future__ import annotations

from pathlib import Path


EXTENSION_SOURCE = Path(__file__).resolve().parents[2] / "helpers" / "gnome_shell_extension" / "extension.js"


def _source() -> str:
    return EXTENSION_SOURCE.read_text(encoding="utf-8")


def test_extension_uses_display_config_monitor_inventory_with_legacy_fallback() -> None:
    source = _source()

    assert "org.gnome.Mutter.DisplayConfig" in source
    assert "GetCurrentState" in source
    assert "_legacyMonitorForIndex" in source
    assert "return this._legacyMonitorForIndex(index) || this._displayConfigMonitorForIndex(index);" in source


def test_extension_skips_redundant_move_resize_when_frame_already_matches() -> None:
    source = _source()

    assert "const currentFrameRect = this._rectPayload(this._safeCall(window, 'get_frame_rect'))" in source
    assert "this._rectsMatchWithinTolerance(currentFrameRect, requestedRect, rectTolerance)" in source
    assert "} else if (typeof window?.move_resize_frame === 'function') {" in source
    assert "window.move_resize_frame(" in source
    assert "window.make_above()" in source


def test_extension_honors_request_rect_tolerance_for_move_resize_noop() -> None:
    source = _source()

    assert "const rectTolerance = this._requestInt(payload, 2, 'rect_tolerance', 'rectTolerance')" in source
    assert "const result = this._applyOverlayPresentation(" in source
    assert "overlayEntry.window," in source
    assert "requestedRect," in source
    assert "rectTolerance," in source
    assert "_rectsMatchWithinTolerance(left, right, tolerance = 0)" in source


def test_extension_gates_target_geometry_diagnostics_behind_query_flag() -> None:
    source = _source()

    assert "include_geometry_diagnostics" in source
    assert "includeGeometryDiagnostics" in source
    assert "if (options.includeGeometryDiagnostics) {" in source
    assert "const queryOptions = this._targetQueryOptions(_query);" in source
    assert "payload.geometryDiagnostics = this._geometryDiagnosticsPayload(window" in source
    assert "get_client_area_rect" in source
    assert "get_work_area_current_monitor" in source
    assert "frame_to_client_area" in source
    assert "helper_selected_content_rect" in source


def test_extension_parses_dbus_string_tuple_queries_for_geometry_diagnostics() -> None:
    source = _source()

    assert "_jsonStringPayload(rawValue)" in source
    assert "let value = this._deepUnpack(rawValue);" in source
    assert "if (Array.isArray(value) && value.length === 1) {" in source
    assert "value = this._deepUnpack(value[0]);" in source
    assert "JSON.parse(this._jsonStringPayload(rawValue))" in source


def test_extension_gates_apply_presentation_diagnostics_behind_request_flag() -> None:
    source = _source()

    assert "include_presentation_diagnostics" in source
    assert "includePresentationDiagnostics" in source
    assert "const includePresentationDiagnostics = this._requestBool(" in source
    assert "includePresentationDiagnostics," in source
    assert "_presentationDiagnosticsPayload({" in source
    assert "moveResizeAction" in source
    assert "preFrameRect" in source
    assert "postFrameRect" in source
    assert "presentation_diagnostics" in source


def test_extension_degrades_apply_presentation_when_readback_mismatches_requested_rect() -> None:
    source = _source()

    assert "!this._rectsMatchWithinTolerance(appliedRect, requestedRect, rectTolerance)" in source
    assert "degradeReasons.push('applied_rect_mismatch');" in source
    assert "const status = degradeReasons.length || unsupportedFeatures.length" in source


def test_extension_gates_presentation_strategy_probe_behind_request_flag() -> None:
    source = _source()

    assert "include_presentation_strategy_diagnostics" in source
    assert "includePresentationStrategyDiagnostics" in source
    assert "presentation_strategy_probe" in source
    assert "presentationStrategyProbe" in source
    assert "_normalisePresentationStrategyProbe(" in source
    assert "return includePresentationStrategyDiagnostics ? 'normal_move_resize' : '';" in source
    assert "if (strategyProbe) {" in source


def test_extension_declares_helper_side_presentation_strategy_names() -> None:
    source = _source()

    for strategy in (
        "normal_move_resize",
        "move_to_monitor_then_resize",
        "resize_then_move_to_monitor",
        "make_fullscreen_then_resize",
        "resize_then_make_fullscreen",
        "fullscreen_only",
    ):
        assert strategy in source
    assert "const PRESENTATION_STRATEGY_PROBES = [" in source
    assert "knownStrategies: PRESENTATION_STRATEGY_PROBES" in source


def test_extension_strategy_probe_requires_borderless_fullscreen_target() -> None:
    source = _source()

    assert "_presentationStrategyEligibility(targetPayload, requestedRect, rectTolerance)" in source
    assert "target_not_fullscreen" in source
    assert "missing_target_content_rect" in source
    assert "missing_target_monitor_rect" in source
    assert "target_content_rect_not_monitor_bounds" in source
    assert "requested_rect_not_monitor_bounds" in source
    assert "if (!diagnostics.eligible) {" in source


def test_extension_strategy_probe_checks_methods_and_captures_errors() -> None:
    source = _source()

    assert "_presentationProbeMethodAvailability(window)" in source
    assert "move_to_monitor: typeof window?.move_to_monitor === 'function'" in source
    assert "move_resize_frame: typeof window?.move_resize_frame === 'function'" in source
    assert "make_fullscreen: typeof window?.make_fullscreen === 'function'" in source
    assert "unmake_fullscreen: typeof window?.unmake_fullscreen === 'function'" in source
    assert "_recordPresentationProbeAction(actions, method, callback)" in source
    assert "error: this._errorMessage(error)" in source


def test_extension_strategy_probe_restores_after_fullscreen_probes() -> None:
    source = _source()

    assert "_strategyUsesFullscreen(normalisedStrategy) && !before.fullscreen" in source
    assert "_restoreAfterFullscreenProbe(window, before, diagnostics.restoration)" in source
    assert "window.unmake_fullscreen();" in source
    assert "restore_move_resize_frame" in source
    assert "restoration.restoredFrame = this._rectsMatchWithinTolerance(" in source


def test_extension_strategy_probe_keeps_normal_apply_path_available() -> None:
    source = _source()

    assert "} else {" in source
    assert "moveResizeAction = 'skipped_matching_frame';" in source
    assert "window.move_resize_frame(" in source
    assert "moveResizeAction = 'move_resize_frame';" in source
    assert "window.make_above()" in source


def test_extension_shell_actor_proof_is_opt_in_and_keeps_normal_apply_path() -> None:
    source = _source()

    assert "shell_actor_proof" in source
    assert "shellActorProof" in source
    assert "shell_actor_proof_action" in source
    assert "shellActorProofAction" in source
    assert "if (shellActorProofRequested || shellActorProofAction) {" in source
    assert "this._handleShellActorProof({" in source
    assert "const result = this._applyOverlayPresentation(" in source
    assert "The proof must not run during normal" not in source


def test_extension_shell_actor_proof_uses_strict_borderless_fullscreen_gate() -> None:
    source = _source()

    assert "_shellActorProofEligibility(targetPayload, requestedRect, rectTolerance)" in source
    assert "target_not_fullscreen" in source
    assert "target_not_on_current_workspace" in source
    assert "target_minimized" in source
    assert "missing_target_content_rect" in source
    assert "missing_target_monitor_rect" in source
    assert "target_content_rect_not_monitor_bounds" in source
    assert "requested_rect_not_target_content_rect" in source
    assert "shell_actor_proof_ineligible" in source


def test_extension_shell_actor_proof_creates_non_reactive_transparent_marker() -> None:
    source = _source()

    assert "new St.Widget({" in source
    assert "new St.Label({" in source
    assert "text: 'EDMC Shell Proof'" in source
    assert "reactive: false" in source
    assert "actor.set_reactive?.(false)" in source
    assert "outline.set_reactive?.(false)" in source
    assert "label.set_reactive?.(false)" in source
    assert "background-color: rgba(0, 0, 0, 0);" in source
    assert "border: 3px solid rgba(0, 255, 180, 0.95)" in source


def test_extension_shell_actor_proof_records_single_parent_layer() -> None:
    source = _source()

    assert "_shellActorProofParent(targetPayload)" in source
    assert "const SHELL_ACTOR_PROOF_PARENT = 'target_window_actor_child';" in source
    assert "_shellActorProofParent(targetPayload)" in source
    assert "const targetActor = this._targetWindowActorForToken(targetPayload?.targetToken || '');" in source
    assert "container: targetActor" in source
    assert "mode: 'target_window_actor_child'" in source
    assert "_targetWindowActorForToken(targetToken = '')" in source
    assert "global.get_window_actors?.() || []" in source
    assert "this._metaWindowForActor(actor)" in source
    assert "this._targetToken(window) === targetToken" in source
    assert "parent.container.add_child(actor)" in source
    assert "actor_parent" in source
    assert "knownParents" not in source
    assert "for (const parent" not in source
    assert "const SHELL_ACTOR_PROOF_PARENT = 'Main.uiGroup';" not in source
    assert "mode: 'main_ui_group'" not in source
    assert "const SHELL_ACTOR_PROOF_PARENT = 'global.top_window_group';" not in source
    assert "mode: 'global_top_window_group'" not in source
    assert "const SHELL_ACTOR_PROOF_PARENT = 'global.stage';" not in source
    assert "mode: 'global_stage'" not in source
    assert "const SHELL_ACTOR_PROOF_PARENT = 'global.window_group';" not in source
    assert "container: global.window_group || null" not in source
    assert "mode: 'global_window_group'" not in source
    assert "Main.layoutManager.addChrome" not in source


def test_extension_shell_actor_group_diagnostics_are_opt_in_and_bounded() -> None:
    source = _source()

    assert "normalisedAction === 'diagnose_groups'" in source
    assert "shell_actor_group_diagnostics" in source
    assert "groupDiagnostics: this._shellActorGroupDiagnostics(targetToken)" in source
    assert "payload.group_diagnostics = groupDiagnostics;" in source
    assert "const SHELL_ACTOR_GROUP_DIAGNOSTIC_CHILD_LIMIT = 12" in source
    assert "const SHELL_ACTOR_GROUP_DIAGNOSTIC_NAMES = [" in source
    for group_name in (
        "global.stage",
        "global.window_group",
        "global.top_window_group",
        "global.overlay_group",
        "global.bottom_window_group",
        "global.background_group",
        "global.screen_group",
    ):
        assert group_name in source
    assert "known_groups: SHELL_ACTOR_GROUP_DIAGNOSTIC_NAMES" in source
    assert "stage_child_order: this._shellActorChildOrder('global.stage', { targetToken })" in source
    assert "ui_group_child_order: this._actorChildOrder(" in source
    assert "window_group_child_order: this._shellActorChildOrder(" in source
    assert "proof_actor: this._shellActorProofDiagnostic()" in source
    assert "target_window_actor: this._targetWindowActorDiagnostic(targetToken)" in source
    assert "parent_index: this._actorIndexInParent(parent, actor)" in source
    assert "sibling_index: parentIndex" in source
    assert "target_token_match: Boolean(targetToken && payload.targetToken === targetToken)" in source
    assert "_windowActorPayload(actor, targetToken = '')" in source
    assert "_metaWindowForActor(actor)" in source
    for window_field in (
        "title: payload.title",
        "wm_class: payload.wmClass",
        "monitor: payload.monitor",
        "fullscreen: payload.fullscreen",
        "workspace: payload.workspace",
        "frame_rect: payload.frameRect",
        "content_rect: payload.contentRect",
    ):
        assert window_field in source
    assert "children_truncated: children.length > SHELL_ACTOR_GROUP_DIAGNOSTIC_CHILD_LIMIT" in source
    assert ".slice(0, SHELL_ACTOR_GROUP_DIAGNOSTIC_CHILD_LIMIT)" in source
    assert "child_count: this._actorChildren(actor).length" in source


def test_extension_shell_actor_proof_cleans_up_and_times_out() -> None:
    source = _source()

    assert "const SHELL_ACTOR_PROOF_TIMEOUT_MS = 5000" in source
    assert "_refreshShellActorProofTimeout()" in source
    assert "GLib.timeout_add(" in source
    assert "this._clearShellActorProof('stale_timeout')" in source
    assert "normalisedAction === 'clear'" in source
    assert "this._clearShellActorProof('explicit_clear')" in source
    assert "this._clearShellActorProof('ineligible_target')" in source
    assert "this._healthService?._clearShellActorProof?.('helper_disable')" in source
    assert "parent.remove_child(proof.actor)" in source
    assert "proof?.actor?.destroy?.()" in source


def test_extension_shell_raster_frame_path_is_opt_in_and_keeps_normal_apply_path() -> None:
    source = _source()

    assert "shell_raster_frame" in source
    assert "shellRasterFrame" in source
    assert "shell_raster_frame_action" in source
    assert "shellRasterFrameAction" in source
    assert "if (shellRasterFrameRequested || shellRasterFrameAction) {" in source
    assert "this._handleShellRasterFrame({" in source
    assert "const result = this._applyOverlayPresentation(" in source


def test_extension_shell_raster_frame_uses_target_window_actor_attachment() -> None:
    source = _source()

    assert "const SHELL_RASTER_FRAME_PARENT = 'target_window_actor_child';" in source
    assert "_showShellRasterFrame({" in source
    assert "const targetActor = this._targetWindowActorForToken(targetPayload?.targetToken || '');" in source
    assert "targetActor.add_child(textureActor);" in source
    assert "actor_parent: actorParent || this._shellRasterFrame?.actorParent || ''" in source
    assert "Main.layoutManager.addChrome" not in source


def test_extension_shell_raster_frame_validates_path_and_png_constraints() -> None:
    source = _source()

    assert "_validateShellRasterFramePath(imagePath, byteSize)" in source
    assert "GLib.path_is_absolute(path)" in source
    assert "path.includes('/../')" in source
    assert "path.toLowerCase().endsWith('.png')" in source
    assert "_shellRasterAllowedCacheDirs()" in source
    assert "path_outside_allowed_cache_dir" in source
    assert "Gio.FileType.REGULAR" in source
    assert "SHELL_RASTER_FRAME_MAX_BYTES" in source
    assert "contentType && contentType !== 'image/png'" in source
    assert "PNG frame must be RGBA" in source
    assert "GdkPixbuf.Pixbuf.new_from_file(imagePath)" in source


def test_extension_shell_raster_frame_uses_strict_borderless_fullscreen_gate() -> None:
    source = _source()

    assert "_shellRasterFrameEligibility(targetPayload, targetRect, frameRect, rectTolerance)" in source
    assert "target_not_fullscreen" in source
    assert "target_not_on_current_workspace" in source
    assert "target_minimized" in source
    assert "missing_target_content_rect" in source
    assert "missing_target_monitor_rect" in source
    assert "target_not_borderless_full_monitor" in source
    assert "target_rect_mismatch" in source
    assert "frame_rect_mismatch" in source
    assert "_rectContains(targetRect, frameRect)" in source


def test_extension_shell_raster_frame_is_non_reactive_and_cleans_up() -> None:
    source = _source()

    assert "const SHELL_RASTER_FRAME_TIMEOUT_MS_DEFAULT = 1500;" in source
    assert "reactive: false" in source
    assert "textureActor.set_reactive?.(false)" in source
    assert "normalisedAction === 'clear'" in source
    assert "this._clearShellRasterFrame('explicit_clear')" in source
    assert "this._clearShellRasterFrame('invalid_frame')" in source
    assert "const cleanupAction = this._clearShellRasterFrame(cleanupReason);" in source
    assert "_refreshShellRasterFrameTimeout(staleTimeoutMs)" in source
    assert "this._clearShellRasterFrame('stale_timeout')" in source
    assert "this._healthService?._clearShellRasterFrame?.('helper_disable')" in source
    assert "this._healthService?._disconnectShellRasterOverviewSignals?.()" in source
    assert "parent.remove_child(frame.actor)" in source
    assert "frame?.actor?.destroy?.()" in source


def test_extension_shell_raster_frame_tracks_session_and_overview_safety() -> None:
    source = _source()

    assert "import * as Main from 'resource:///org/gnome/shell/ui/main.js';" in source
    assert "_shellRasterSessionIdFromVersion(frameVersion)" in source
    assert "session_generation_mismatch" in source
    assert "session_id:" in source
    assert "_shellRasterFrameFocusRiskReason(targetPayload, allowUnfocusedTarget)" in source
    assert "'allow_unfocused_target'" in source
    assert "'allowUnfocusedTarget'" in source
    assert "!allowUnfocusedTarget && targetPayload && targetPayload.hasFocus === false" in source
    assert "allow_unfocused_target: Boolean(allowUnfocusedTarget)" in source
    assert "gnome_overview_active" in source
    assert "target_not_focused" in source
    assert "_connectShellRasterOverviewSignals()" in source
    assert "_disconnectShellRasterOverviewSignals()" in source
    assert "overview.connect(signalName" in source


def test_extension_shell_raster_frame_reports_debug_timing_diagnostics() -> None:
    source = _source()

    assert "'shell_raster_frame_diagnostics'" in source
    assert "'shellRasterFrameDiagnostics'" in source
    assert "_requestObject(payload" in source
    assert "_shellRasterFrameDiagnostics(requestDiagnostics, helperTiming)" in source
    assert "helper_decode_ms" in source
    assert "helper_apply_ms" in source
    assert "helper_total_ms" in source
    assert "timing: this._shellRasterHelperTiming(totalStartedUs" in source


def test_extension_shell_raster_frame_reuses_unchanged_frame_before_decode() -> None:
    source = _source()

    reuse_call = source.index("const reusableFrame = this._reuseShellRasterFrameIfMatching({")
    clear_existing = source.index("const cleanupReason = this._shellRasterFrame?.sessionId")
    decode_load = source.index("const loaded = this._loadShellRasterTextureActor(imagePath);")
    assert reuse_call < clear_existing < decode_load
    assert "if (reusableFrame) {" in source
    assert "return reusableFrame;" in source
    assert "_shellRasterFrameIdentityMatches(frame" in source


def test_extension_shell_raster_frame_identity_requires_same_frame_and_rects() -> None:
    source = _source()

    assert "String(frame.frameVersion || '') === String(frameVersion || '')" in source
    assert "String(frame.checksum || '') === String(checksum || '')" in source
    assert "String(frame.imagePath || '') === String(imagePath || '')" in source
    assert "Number(frame.byteSize || 0) === Number(byteSize || 0)" in source
    assert "String(frame.targetToken || '') === String(targetToken || '')" in source
    assert "this._rectsMatchWithinTolerance(frame.targetRect, targetRect, 0)" in source
    assert "this._rectsMatchWithinTolerance(frame.frameRect, frameRect, 0)" in source
    assert "frame.actor.get_parent() !== targetActor" in source


def test_extension_shell_raster_frame_reuse_reports_decode_skip_diagnostics() -> None:
    source = _source()

    assert "updateReason: 'reused_existing_frame'" in source
    assert "decodeSkipped: true" in source
    assert "reusedFrame: true" in source
    assert "helper_reused_frame" in source
    assert "helper_decode_skipped" in source
    assert "helper_update_reason" in source
    assert "update_reason: updateReason" in source
