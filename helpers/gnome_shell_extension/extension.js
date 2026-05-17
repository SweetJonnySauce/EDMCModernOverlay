import Clutter from 'gi://Clutter';
import Cogl from 'gi://Cogl';
import Gio from 'gi://Gio';
import GdkPixbuf from 'gi://GdkPixbuf';
import GLib from 'gi://GLib';
import Shell from 'gi://Shell';
import St from 'gi://St';
import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

import {
    HELPER_CAPABILITIES,
    HELPER_COORDINATE_SPACE,
    HELPER_DBUS_HEALTH_METHOD,
    HELPER_DBUS_HELLO_METHOD,
    HELPER_DBUS_INTERFACE,
    HELPER_DBUS_OBJECT_PATH,
    HELPER_DBUS_PRESENTATION_METHOD,
    HELPER_DBUS_SERVICE,
    HELPER_DBUS_TARGET_METHOD,
    HELPER_KIND,
    HELPER_PROTOCOL,
    HELPER_UUID,
    HELPER_VERSION,
} from './constants.js';

const HELPER_DBUS_XML = `
<node>
  <interface name="${HELPER_DBUS_INTERFACE}">
    <method name="${HELPER_DBUS_HELLO_METHOD}">
      <arg type="s" name="client" direction="in"/>
      <arg type="s" name="health" direction="out"/>
    </method>
    <method name="${HELPER_DBUS_HEALTH_METHOD}">
      <arg type="s" name="health" direction="out"/>
    </method>
    <method name="${HELPER_DBUS_TARGET_METHOD}">
      <arg type="s" name="query" direction="in"/>
      <arg type="s" name="target_state" direction="out"/>
    </method>
    <method name="${HELPER_DBUS_PRESENTATION_METHOD}">
      <arg type="s" name="request" direction="in"/>
      <arg type="s" name="presentation_state" direction="out"/>
    </method>
  </interface>
</node>`;

const DISPLAY_CONFIG_DBUS_SERVICE = 'org.gnome.Mutter.DisplayConfig';
const DISPLAY_CONFIG_DBUS_OBJECT_PATH = '/org/gnome/Mutter/DisplayConfig';
const DISPLAY_CONFIG_DBUS_INTERFACE = 'org.gnome.Mutter.DisplayConfig';
const DISPLAY_CONFIG_GET_CURRENT_STATE_METHOD = 'GetCurrentState';
const DISPLAY_CONFIG_MONITOR_CACHE_TTL_US = 1000000;
const DISPLAY_CONFIG_DBUS_TIMEOUT_MS = 250;
const SHELL_ACTOR_PROOF_TIMEOUT_MS = 5000;
const SHELL_RASTER_FRAME_TIMEOUT_MS_DEFAULT = 1500;
const SHELL_RASTER_FRAME_MAX_BYTES = 8 * 1024 * 1024;
const SHELL_RASTER_FRAME_RENDERER = 'gnome_shell_raster_frame';
const SHELL_RASTER_FRAME_PARENT = 'target_window_actor_child';
const SHELL_ACTOR_GROUP_DIAGNOSTIC_CHILD_LIMIT = 12;
const SHELL_ACTOR_PROOF_PARENT = 'target_window_actor_child';
const SHELL_ACTOR_GROUP_DIAGNOSTIC_NAMES = [
    'global.stage',
    'global.window_group',
    'global.top_window_group',
    'global.overlay_group',
    'global.bottom_window_group',
    'global.background_group',
    'global.screen_group',
];
const PRESENTATION_STRATEGY_PROBES = [
    'normal_move_resize',
    'move_to_monitor_then_resize',
    'resize_then_move_to_monitor',
    'make_fullscreen_then_resize',
    'resize_then_make_fullscreen',
    'fullscreen_only',
];

class HelperHealthService {
    constructor() {
        this._startedAtUnixMs = Date.now();
        this._startedAtMonotonicUs = GLib.get_monotonic_time();
        this._targetSequence = 0;
        this._presentationSequence = 0;
        this._displayConfigMonitorCache = null;
        this._displayConfigMonitorCacheExpiresUs = 0;
        this._shellActorProof = null;
        this._shellActorProofTimeoutId = 0;
        this._shellRasterFrame = null;
        this._shellRasterRegions = new Map();
        this._shellRasterFrameTimeoutId = 0;
        this._shellRasterOverviewSignalIds = [];
        this._connectShellRasterOverviewSignals();
    }

    Hello(_client) {
        return this.GetHealth();
    }

    GetHealth() {
        return JSON.stringify({
            status: 'healthy',
            uuid: HELPER_UUID,
            helper_kind: HELPER_KIND,
            helper_version: HELPER_VERSION,
            helper_protocol: HELPER_PROTOCOL,
            capabilities: HELPER_CAPABILITIES,
            service_name: HELPER_DBUS_SERVICE,
            object_path: HELPER_DBUS_OBJECT_PATH,
            interface_name: HELPER_DBUS_INTERFACE,
            started_at_unix_ms: this._startedAtUnixMs,
            started_at_monotonic_us: this._startedAtMonotonicUs,
            generated_at_unix_ms: Date.now(),
            generated_at_monotonic_us: GLib.get_monotonic_time(),
        });
    }

    GetTargetState(_query) {
        this._targetSequence += 1;
        const generatedAtUnixMs = Date.now();
        const generatedAtMonotonicUs = GLib.get_monotonic_time();
        const queryOptions = this._targetQueryOptions(_query);
        const windows = this._enumerateWindows(queryOptions);
        const selection = this._selectEliteTarget(windows);
        return JSON.stringify({
            status: selection.status,
            helper_kind: HELPER_KIND,
            helper_version: HELPER_VERSION,
            helper_protocol: HELPER_PROTOCOL,
            coordinate_space: HELPER_COORDINATE_SPACE,
            sequence: this._targetSequence,
            generated_at_unix_ms: generatedAtUnixMs,
            generated_at_monotonic_us: generatedAtMonotonicUs,
            candidate_count: selection.candidateCount,
            launcher_count: selection.launcherCount,
            detail: selection.detail,
            target: selection.target,
        });
    }

    ApplyPresentation(request) {
        this._presentationSequence += 1;
        const generatedAtUnixMs = Date.now();
        const generatedAtMonotonicUs = GLib.get_monotonic_time();
        const parsed = this._parseJsonObject(request);
        if (!parsed.ok) {
            return JSON.stringify(this._presentationPayload({
                status: 'malformed_payload',
                action: 'degrade',
                generatedAtUnixMs,
                generatedAtMonotonicUs,
                detail: parsed.detail,
                degradeReasons: ['malformed_payload'],
            }));
        }

        const payload = parsed.value;
        const action = this._requestString(payload, 'action') || 'degrade';
        const targetToken = this._requestString(payload, 'target_token', 'targetToken');
        const requestedRect = this._requestRect(payload, 'content_rect', 'contentRect');
        const rectTolerance = this._requestInt(payload, 2, 'rect_tolerance', 'rectTolerance');
        const standaloneMode = this._requestBool(payload, 'standalone_mode', 'standaloneMode');
        const includePresentationDiagnostics = this._requestBool(
            payload,
            'include_presentation_diagnostics',
            'includePresentationDiagnostics',
            'presentationDiagnostics',
        );
        const includePresentationStrategyDiagnostics = this._requestBool(
            payload,
            'include_presentation_strategy_diagnostics',
            'includePresentationStrategyDiagnostics',
        );
        const presentationStrategyProbe = this._requestString(
            payload,
            'presentation_strategy_probe',
            'presentationStrategyProbe',
        );
        const shellActorProofRequested = this._requestBool(payload, 'shell_actor_proof', 'shellActorProof');
        const shellActorProofAction = this._requestString(
            payload,
            'shell_actor_proof_action',
            'shellActorProofAction',
        );
        const shellRasterFrameRequested = this._requestBool(payload, 'shell_raster_frame', 'shellRasterFrame');
        const shellRasterFrameAction = this._requestString(
            payload,
            'shell_raster_frame_action',
            'shellRasterFrameAction',
        );
        const base = {
            action,
            targetToken,
            requestedRect,
            standaloneMode,
            generatedAtUnixMs,
            generatedAtMonotonicUs,
        };

        if (shellRasterFrameRequested || shellRasterFrameAction) {
            return JSON.stringify(this._handleShellRasterFrame({
                ...base,
                payload,
                frameAction: shellRasterFrameAction || 'update',
                rectTolerance,
            }));
        }

        if (shellActorProofRequested || shellActorProofAction) {
            return JSON.stringify(this._handleShellActorProof({
                ...base,
                proofAction: shellActorProofAction || 'show',
                rectTolerance,
            }));
        }

        if (action === 'hide') {
            return JSON.stringify(this._presentationPayload({
                ...base,
                status: 'presentation_hidden',
                detail: 'target hidden',
                degradeReasons: ['target_hidden'],
            }));
        }
        if (action === 'degrade') {
            return JSON.stringify(this._presentationPayload({
                ...base,
                status: 'presentation_degraded',
                detail: 'client requested degrade',
                degradeReasons: this._requestStringList(payload, 'degrade_reasons', 'degradeReasons'),
            }));
        }
        if (action !== 'attach') {
            return JSON.stringify(this._presentationPayload({
                ...base,
                status: 'malformed_payload',
                action: 'degrade',
                detail: `unsupported action=${action}`,
                degradeReasons: ['unsupported_action'],
            }));
        }
        if (!targetToken || !this._rectIsValid(requestedRect)) {
            return JSON.stringify(this._presentationPayload({
                ...base,
                status: 'malformed_payload',
                action: 'degrade',
                detail: 'attach requires target token and content rect',
                degradeReasons: ['missing_target_or_rect'],
            }));
        }

        const windows = this._enumerateWindowEntries();
        const targetEntry = windows.find(entry => entry.payload.targetToken === targetToken);
        if (!targetEntry || !this._isEliteClient(targetEntry.payload)) {
            return JSON.stringify(this._presentationPayload({
                ...base,
                status: 'target_unavailable',
                detail: 'target unavailable',
                degradeReasons: ['target_unavailable'],
            }));
        }
        if (targetEntry.payload.minimized || !targetEntry.payload.showingOnWorkspace) {
            return JSON.stringify(this._presentationPayload({
                ...base,
                status: 'target_hidden',
                detail: 'target hidden',
                degradeReasons: ['target_hidden'],
            }));
        }

        const overlayEntry = this._findOverlayWindow(windows, payload, targetToken);
        if (!overlayEntry) {
            return JSON.stringify(this._presentationPayload({
                ...base,
                status: 'presentation_degraded',
                detail: 'overlay window not found',
                degradeReasons: ['overlay_window_not_found'],
            }));
        }

        const result = this._applyOverlayPresentation(
            overlayEntry.window,
            requestedRect,
            rectTolerance,
            {
                includePresentationDiagnostics,
                includePresentationStrategyDiagnostics,
                presentationStrategyProbe,
                overlayPayload: overlayEntry.payload,
                targetPayload: targetEntry.payload,
            },
        );
        const chromeFree = this._windowChromeFree(overlayEntry.payload);
        const clickThrough = this._requestBool(payload, 'click_through_expected', 'clickThroughExpected');
        const focusSafe = result.stacking && clickThrough;
        const unsupportedFeatures = [...result.unsupportedFeatures];
        const degradeReasons = [...result.degradeReasons];
        if (!chromeFree) {
            degradeReasons.push('chrome_free_unproven');
        }
        if (!clickThrough) {
            degradeReasons.push('click_through_unproven');
        }
        if (!focusSafe) {
            degradeReasons.push('focus_safe_unproven');
        }
        if (standaloneMode) {
            degradeReasons.push('standalone_mode_enabled');
        }
        const status = degradeReasons.length || unsupportedFeatures.length
            ? 'presentation_degraded'
            : 'presentation_applied';

        return JSON.stringify(this._presentationPayload({
            ...base,
            status,
            overlayToken: overlayEntry.payload.targetToken,
            appliedRect: result.appliedRect,
            placement: result.placement,
            chromeFree,
            stacking: result.stacking,
            clickThrough,
            focusSafe,
            standaloneMode,
            unsupportedFeatures,
            degradeReasons,
            presentationDiagnostics: result.presentationDiagnostics,
            detail: status === 'presentation_applied' ? '' : 'required presentation gate unproven',
        }));
    }

    _enumerateWindows(options = {}) {
        return this._enumerateWindowEntries(options).map(entry => entry.payload);
    }

    _enumerateWindowEntries(options = {}) {
        const tracker = Shell.WindowTracker.get_default();
        return global.get_window_actors()
            .map(actor => actor?.get_meta_window?.())
            .filter(window => window)
            .map(window => ({
                window,
                payload: this._windowPayload(window, tracker, options),
            }));
    }

    _windowPayload(window, tracker, options = {}) {
        const app = tracker?.get_window_app?.(window);
        const frameRect = this._rectPayload(this._safeCall(window, 'get_frame_rect'));
        const bufferRect = this._rectPayload(this._safeCall(window, 'get_buffer_rect'));
        const contentRect = this._contentRectPayload(window, frameRect, bufferRect);
        const monitor = this._safeCall(window, 'get_monitor');
        const monitorInfo = this._monitorForIndex(monitor);
        const monitorRect = this._rectPayload(monitorInfo);
        const payload = {
            targetToken: this._targetToken(window),
            title: String(this._safeCall(window, 'get_title') || ''),
            wmClass: String(this._safeCall(window, 'get_wm_class') || ''),
            wmClassInstance: String(this._safeCall(window, 'get_wm_class_instance') || ''),
            appId: String(app?.get_id?.() || ''),
            appName: String(app?.get_name?.() || ''),
            pid: this._safeCall(window, 'get_pid') || null,
            windowType: this._safeCall(window, 'get_window_type'),
            frameRect,
            bufferRect,
            contentRect,
            decorationInsets: this._decorationInsets(frameRect, contentRect),
            monitor,
            outputName: this._monitorOutputName(monitorInfo),
            monitorRect,
            monitorScale: this._monitorScale(monitorInfo),
            hasFocus: Boolean(window?.has_focus?.()),
            showingOnWorkspace: Boolean(window?.showing_on_its_workspace?.()),
            minimized: Boolean(window?.minimized),
            fullscreen: Boolean(window?.fullscreen || window?.is_fullscreen?.()),
            workspace: this._workspaceName(window),
        };
        if (options.includeGeometryDiagnostics) {
            payload.geometryDiagnostics = this._geometryDiagnosticsPayload(window, {
                frameRect,
                bufferRect,
                contentRect,
                monitor,
                monitorRect,
                monitorInfo,
            });
        }
        return payload;
    }

    _selectEliteTarget(windows) {
        const clients = [];
        let launcherCount = 0;
        for (const window of windows) {
            if (this._isLauncher(window)) {
                launcherCount += 1;
                continue;
            }
            if (!this._isEliteClient(window)) {
                continue;
            }
            clients.push({ score: this._scoreTarget(window), target: window });
        }
        if (clients.length === 0) {
            return {
                status: launcherCount > 0 ? 'launcher_only' : 'target_not_found',
                target: null,
                candidateCount: 0,
                launcherCount,
                detail: '',
            };
        }
        clients.sort((left, right) => right.score - left.score);
        if (clients.length > 1 && clients[0].score === clients[1].score) {
            return {
                status: 'target_ambiguous',
                target: null,
                candidateCount: clients.length,
                launcherCount,
                detail: 'multiple_equal_elite_candidates',
            };
        }
        return {
            status: 'target_found',
            target: clients[0].target,
            candidateCount: clients.length,
            launcherCount,
            detail: '',
        };
    }

    _isEliteClient(window) {
        const title = String(window.title || '').toLowerCase();
        return title.includes('elite') &&
            title.includes('dangerous') &&
            !this._isLauncher(window) &&
            !window.minimized &&
            this._rectIsValid(window.frameRect);
    }

    _isLauncher(window) {
        const title = String(window.title || '').toLowerCase();
        return title.includes('elite') &&
            (title.includes('launcher') || title.includes('installer') || title.includes('updater'));
    }

    _scoreTarget(window) {
        let score = 100;
        const title = String(window.title || '').toLowerCase();
        const identifiers = [
            String(window.wmClass || '').toLowerCase(),
            String(window.appName || '').toLowerCase(),
            String(window.appId || '').toLowerCase(),
        ];
        if (title.includes('(client)')) {
            score += 20;
        }
        if (identifiers.includes('steam_app_359320')) {
            score += 10;
        }
        if (window.showingOnWorkspace) {
            score += 10;
        }
        if (window.hasFocus) {
            score += 5;
        }
        if (window.pid !== null && window.pid !== undefined) {
            score += 1;
        }
        return score;
    }

    _targetToken(window) {
        const stableSequence = window?.get_stable_sequence?.();
        if (stableSequence !== null && stableSequence !== undefined) {
            return `meta:${stableSequence}`;
        }
        const pid = this._safeCall(window, 'get_pid') || 'unknown';
        const title = String(this._safeCall(window, 'get_title') || 'untitled');
        return `window:${pid}:${title}`;
    }

    _contentRectPayload(window, frameRect, bufferRect) {
        const clientRect = this._rectPayload(this._safeCall(window, 'get_client_area_rect'));
        if (clientRect && this._rectIsValid(clientRect)) {
            return clientRect;
        }
        if (frameRect && bufferRect && this._rectsEqual(frameRect, bufferRect)) {
            return frameRect;
        }
        return null;
    }

    _decorationInsets(frameRect, contentRect) {
        if (!frameRect || !contentRect) {
            return null;
        }
        return this._rectInsets(frameRect, contentRect);
    }

    _rectInsets(outerRect, innerRect) {
        if (!outerRect || !innerRect) {
            return null;
        }
        return {
            left: innerRect.x - outerRect.x,
            top: innerRect.y - outerRect.y,
            right: (outerRect.x + outerRect.width) - (innerRect.x + innerRect.width),
            bottom: (outerRect.y + outerRect.height) - (innerRect.y + innerRect.height),
        };
    }

    _targetQueryOptions(rawQuery) {
        const parsed = this._parseJsonObject(rawQuery);
        const query = parsed.ok ? parsed.value : {};
        return {
            includeGeometryDiagnostics: this._requestBool(
                query,
                'include_geometry_diagnostics',
                'includeGeometryDiagnostics',
                'geometryDiagnostics',
            ),
        };
    }

    _geometryDiagnosticsPayload(window, context) {
        const frameRect = context.frameRect;
        const bufferRect = context.bufferRect;
        const clientAreaRect = this._rectPayload(this._safeCall(window, 'get_client_area_rect'));
        const workAreaRect = this._rectPayload(this._safeCall(window, 'get_work_area_current_monitor'));
        const contentRect = context.contentRect;
        return {
            schema: 1,
            candidates: {
                frame: this._geometryCandidatePayload(window, 'frame', 'get_frame_rect', frameRect),
                buffer: this._geometryCandidatePayload(window, 'buffer', 'get_buffer_rect', bufferRect),
                client_area: this._geometryCandidatePayload(
                    window,
                    'client_area',
                    'get_client_area_rect',
                    clientAreaRect,
                ),
                work_area_current_monitor: this._geometryCandidatePayload(
                    window,
                    'work_area_current_monitor',
                    'get_work_area_current_monitor',
                    workAreaRect,
                ),
                selected_content: {
                    name: 'selected_content',
                    method: 'helper_selected_content_rect',
                    available: Boolean(contentRect),
                    valid: this._rectIsValid(contentRect),
                    rect: contentRect,
                },
            },
            insets: {
                frame_to_buffer: this._geometryInsetPayload('frame', frameRect, 'buffer', bufferRect),
                frame_to_client_area: this._geometryInsetPayload(
                    'frame',
                    frameRect,
                    'client_area',
                    clientAreaRect,
                ),
                frame_to_selected_content: this._geometryInsetPayload(
                    'frame',
                    frameRect,
                    'selected_content',
                    contentRect,
                ),
            },
            monitor: {
                index: context.monitor,
                rect: context.monitorRect,
                outputName: this._monitorOutputName(context.monitorInfo),
                scale: this._monitorScale(context.monitorInfo),
            },
            state: {
                hasFocus: Boolean(window?.has_focus?.()),
                showingOnWorkspace: Boolean(window?.showing_on_its_workspace?.()),
                minimized: Boolean(window?.minimized),
                fullscreen: Boolean(window?.fullscreen || window?.is_fullscreen?.()),
                workspace: this._workspaceName(window),
            },
        };
    }

    _geometryCandidatePayload(window, name, method, rect) {
        return {
            name,
            method,
            available: typeof window?.[method] === 'function',
            valid: this._rectIsValid(rect),
            rect,
        };
    }

    _geometryInsetPayload(source, sourceRect, target, targetRect) {
        const valid = this._rectIsValid(sourceRect) && this._rectIsValid(targetRect);
        return {
            name: `${source}_to_${target}`,
            source,
            target,
            valid,
            insets: valid ? this._rectInsets(sourceRect, targetRect) : null,
        };
    }

    _rectPayload(rect) {
        if (!rect) {
            return null;
        }
        return {
            x: Number(rect.x),
            y: Number(rect.y),
            width: Number(rect.width),
            height: Number(rect.height),
        };
    }

    _rectIsValid(rect) {
        return Boolean(rect && rect.width > 0 && rect.height > 0);
    }

    _rectsEqual(left, right) {
        return left.x === right.x &&
            left.y === right.y &&
            left.width === right.width &&
            left.height === right.height;
    }

    _rectsMatchWithinTolerance(left, right, tolerance = 0) {
        if (!this._rectIsValid(left) || !this._rectIsValid(right)) {
            return false;
        }
        const allowed = Math.max(0, Number(tolerance) || 0);
        return Math.abs(left.x - right.x) <= allowed &&
            Math.abs(left.y - right.y) <= allowed &&
            Math.abs(left.width - right.width) <= allowed &&
            Math.abs(left.height - right.height) <= allowed;
    }

    _safeCall(object, methodName) {
        try {
            if (!object || typeof object[methodName] !== 'function') {
                return null;
            }
            return object[methodName]();
        } catch (_error) {
            return null;
        }
    }

    _monitorOutputName(monitor) {
        return String(monitor?.connector || monitor?.get_connector?.() || '');
    }

    _monitorScale(monitor) {
        const scale = monitor?.scale_factor ?? monitor?.scale ?? monitor?.get_scale_factor?.();
        const numericScale = Number(scale);
        return Number.isFinite(numericScale) && numericScale > 0 ? numericScale : null;
    }

    _monitorForIndex(monitorIndex) {
        const index = this._normaliseMonitorIndex(monitorIndex);
        if (index === null) {
            return null;
        }
        return this._legacyMonitorForIndex(index) || this._displayConfigMonitorForIndex(index);
    }

    _normaliseMonitorIndex(monitorIndex) {
        const index = Number(monitorIndex);
        return Number.isInteger(index) && index >= 0 ? index : null;
    }

    _displayConfigMonitorForIndex(monitorIndex) {
        const monitors = this._displayConfigMonitors();
        return monitors[monitorIndex] || null;
    }

    _displayConfigMonitors() {
        const now = GLib.get_monotonic_time();
        if (this._displayConfigMonitorCache && now < this._displayConfigMonitorCacheExpiresUs) {
            return this._displayConfigMonitorCache;
        }
        const monitors = this._fetchDisplayConfigMonitors();
        this._displayConfigMonitorCache = monitors;
        this._displayConfigMonitorCacheExpiresUs = now + DISPLAY_CONFIG_MONITOR_CACHE_TTL_US;
        return monitors;
    }

    _fetchDisplayConfigMonitors() {
        try {
            const state = Gio.DBus.session.call_sync(
                DISPLAY_CONFIG_DBUS_SERVICE,
                DISPLAY_CONFIG_DBUS_OBJECT_PATH,
                DISPLAY_CONFIG_DBUS_INTERFACE,
                DISPLAY_CONFIG_GET_CURRENT_STATE_METHOD,
                null,
                null,
                Gio.DBusCallFlags.NONE,
                DISPLAY_CONFIG_DBUS_TIMEOUT_MS,
                null
            );
            return this._parseDisplayConfigMonitors(this._deepUnpack(state));
        } catch (_error) {
            return [];
        }
    }

    _parseDisplayConfigMonitors(state) {
        const physicalMonitors = this._deepUnpack(state?.[1]);
        const logicalMonitors = this._deepUnpack(state?.[2]);
        if (!Array.isArray(physicalMonitors) || !Array.isArray(logicalMonitors)) {
            return [];
        }
        const physicalModes = this._displayConfigPhysicalModes(physicalMonitors);
        return logicalMonitors.map(logicalMonitor =>
            this._displayConfigLogicalMonitor(logicalMonitor, physicalModes)
        );
    }

    _displayConfigPhysicalModes(physicalMonitors) {
        const modes = new Map();
        for (const physicalMonitor of physicalMonitors) {
            const monitorSpec = this._deepUnpack(physicalMonitor?.[0]);
            const connector = String(monitorSpec?.[0] || '');
            const currentMode = this._currentDisplayConfigMode(physicalMonitor?.[1]);
            if (connector && currentMode) {
                modes.set(connector, currentMode);
            }
        }
        return modes;
    }

    _currentDisplayConfigMode(modes) {
        const unpackedModes = this._deepUnpack(modes);
        if (!Array.isArray(unpackedModes)) {
            return null;
        }
        for (const mode of unpackedModes) {
            const properties = this._deepUnpack(mode?.[6]);
            if (!this._variantBool(properties?.['is-current'])) {
                continue;
            }
            const width = Number(mode?.[1]);
            const height = Number(mode?.[2]);
            if (Number.isFinite(width) && width > 0 && Number.isFinite(height) && height > 0) {
                return { width, height };
            }
        }
        return null;
    }

    _displayConfigLogicalMonitor(logicalMonitor, physicalModes) {
        const monitor = this._deepUnpack(logicalMonitor);
        const x = Number(monitor?.[0]);
        const y = Number(monitor?.[1]);
        const scale = this._normaliseScale(monitor?.[2]);
        const transform = Number(monitor?.[3] ?? 0);
        const monitorSpecs = this._deepUnpack(monitor?.[5]);
        const firstSpec = this._deepUnpack(Array.isArray(monitorSpecs) ? monitorSpecs[0] : null);
        const connector = String(firstSpec?.[0] || '');
        const mode = physicalModes.get(connector);
        if (!mode || !Number.isFinite(x) || !Number.isFinite(y)) {
            return null;
        }

        let width = mode.width;
        let height = mode.height;
        if (this._transformRotatesMonitor(transform)) {
            [width, height] = [height, width];
        }
        width = Math.round(width / scale);
        height = Math.round(height / scale);
        if (width <= 0 || height <= 0) {
            return null;
        }
        return {
            x,
            y,
            width,
            height,
            connector,
            scale_factor: scale,
        };
    }

    _normaliseScale(scale) {
        const numericScale = Number(scale);
        return Number.isFinite(numericScale) && numericScale > 0 ? numericScale : 1;
    }

    _transformRotatesMonitor(transform) {
        return transform === 1 || transform === 3 || transform === 5 || transform === 7;
    }

    _variantBool(value) {
        return Boolean(this._deepUnpack(value));
    }

    _deepUnpack(value) {
        try {
            return value && typeof value.deepUnpack === 'function' ? value.deepUnpack() : value;
        } catch (_error) {
            return value;
        }
    }

    _legacyMonitorForIndex(monitorIndex) {
        try {
            if (!global.display?.get_monitor_geometry) {
                return null;
            }
            const geometry = global.display.get_monitor_geometry(monitorIndex);
            if (!geometry) {
                return null;
            }
            const scale = global.display?.get_monitor_scale?.(monitorIndex);
            return {
                x: Number(geometry.x),
                y: Number(geometry.y),
                width: Number(geometry.width),
                height: Number(geometry.height),
                scale_factor: scale,
            };
        } catch (_error) {
            return null;
        }
    }

    _workspaceName(window) {
        try {
            const workspace = window?.get_workspace?.();
            return String(workspace?.index?.() ?? '');
        } catch (_error) {
            return '';
        }
    }

    _presentationPayload({
        status,
        action = 'degrade',
        targetToken = '',
        overlayToken = '',
        requestedRect = null,
        appliedRect = null,
        renderer = 'pyqt',
        placement = false,
        chromeFree = false,
        stacking = false,
        clickThrough = false,
        focusSafe = false,
        standaloneMode = false,
        unsupportedFeatures = [],
        degradeReasons = [],
        generatedAtUnixMs = Date.now(),
        generatedAtMonotonicUs = GLib.get_monotonic_time(),
        presentationDiagnostics = null,
        shellActorProof = null,
        shellRasterFrame = null,
        frameVersion = '',
        frameRect = null,
        frameDimensions = null,
        cleanupAction = '',
        detail = '',
    }) {
        const payload = {
            status,
            helper_kind: HELPER_KIND,
            helper_version: HELPER_VERSION,
            helper_protocol: HELPER_PROTOCOL,
            coordinate_space: HELPER_COORDINATE_SPACE,
            action,
            target_token: targetToken,
            overlay_token: overlayToken,
            requested_rect: requestedRect,
            applied_rect: appliedRect,
            renderer,
            placement,
            chrome_free: chromeFree,
            stacking,
            click_through: clickThrough,
            focus_safe: focusSafe,
            standalone_mode: standaloneMode,
            unsupported_features: unsupportedFeatures,
            degrade_reasons: degradeReasons,
            sequence: this._presentationSequence,
            generated_at_unix_ms: generatedAtUnixMs,
            generated_at_monotonic_us: generatedAtMonotonicUs,
            detail,
        };
        if (frameVersion) {
            payload.frame_version = frameVersion;
        }
        if (frameRect) {
            payload.frame_rect = frameRect;
        }
        if (frameDimensions) {
            payload.frame_dimensions = frameDimensions;
        }
        if (cleanupAction) {
            payload.cleanup_action = cleanupAction;
        }
        if (presentationDiagnostics) {
            payload.presentation_diagnostics = presentationDiagnostics;
        }
        if (shellActorProof) {
            payload.shell_actor_proof = shellActorProof;
        }
        if (shellRasterFrame) {
            payload.shell_raster_frame = shellRasterFrame;
        }
        return payload;
    }

    _handleShellRasterFrame({
        action,
        targetToken,
        requestedRect,
        standaloneMode,
        generatedAtUnixMs,
        generatedAtMonotonicUs,
        payload,
        frameAction,
        rectTolerance,
    }) {
        const normalisedAction = String(frameAction || 'update').trim().toLowerCase();
        if (normalisedAction === 'clear') {
            const cleanupAction = this._clearShellRasterFrame('explicit_clear');
            return this._presentationPayload({
                status: 'shell_raster_frame_cleared',
                action,
                targetToken,
                requestedRect,
                standaloneMode,
                generatedAtUnixMs,
                generatedAtMonotonicUs,
                renderer: SHELL_RASTER_FRAME_RENDERER,
                cleanupAction,
                shellRasterFrame: this._shellRasterFramePayload({
                    requestedAction: normalisedAction,
                    visible: false,
                    targetToken,
                    requestedRect,
                    cleanupAction,
                }),
            });
        }
        if (normalisedAction !== 'update') {
            return this._presentationPayload({
                status: 'malformed_payload',
                action: 'degrade',
                targetToken,
                requestedRect,
                standaloneMode,
                generatedAtUnixMs,
                generatedAtMonotonicUs,
                renderer: SHELL_RASTER_FRAME_RENDERER,
                degradeReasons: ['unsupported_shell_raster_frame_action'],
                detail: `unsupported shell raster frame action=${normalisedAction}`,
                shellRasterFrame: this._shellRasterFramePayload({
                    requestedAction: normalisedAction,
                    visible: Boolean(this._shellRasterFrame?.actor),
                    targetToken,
                    requestedRect,
                    eligible: false,
                    eligibilityReasons: ['unsupported_shell_raster_frame_action'],
                }),
            });
        }

        const targetRect = this._requestRect(payload, 'target_rect', 'targetRect') || requestedRect;
        const frameRect = this._requestRect(payload, 'frame_rect', 'frameRect');
        const frameVersion = this._requestString(payload, 'frame_version', 'frameVersion');
        const imagePath = this._requestString(payload, 'image_path', 'imagePath');
        const checksum = this._requestString(payload, 'checksum');
        const byteSize = this._requestInt(payload, 0, 'byte_size', 'byteSize');
        const frameRegions = this._shellRasterFrameRegionsFromPayload({
            regions: this._requestArray(payload, 'shell_raster_regions', 'shellRasterRegions'),
            targetToken,
            targetRect,
        });
        const allowUnfocusedTarget = this._requestBool(
            payload,
            'allow_unfocused_target',
            'allowUnfocusedTarget',
        );
        const staleTimeoutMs = Math.max(
            1000,
            this._requestInt(payload, SHELL_RASTER_FRAME_TIMEOUT_MS_DEFAULT, 'stale_timeout_ms', 'staleTimeoutMs'),
        );
        const requestDiagnostics = this._requestObject(
            payload,
            'shell_raster_frame_diagnostics',
            'shellRasterFrameDiagnostics',
        );
        const multiRegionRequested = frameRegions.length > 0;

        const windows = this._enumerateWindowEntries();
        const targetEntry = windows.find(entry => entry.payload.targetToken === targetToken);
        const targetPayload = targetEntry?.payload || null;
        const focusRiskReason = this._shellRasterFrameFocusRiskReason(targetPayload, allowUnfocusedTarget);
        if (focusRiskReason) {
            const cleanupAction = this._clearShellRasterFrame(focusRiskReason);
            return this._presentationPayload({
                status: 'presentation_degraded',
                action,
                targetToken,
                requestedRect: targetRect,
                appliedRect: null,
                standaloneMode,
                generatedAtUnixMs,
                generatedAtMonotonicUs,
                renderer: SHELL_RASTER_FRAME_RENDERER,
                degradeReasons: [focusRiskReason],
                cleanupAction,
                detail: 'shell raster frame suspended for focus/overview safety',
                shellRasterFrame: this._shellRasterFramePayload({
                    requestedAction: normalisedAction,
                    visible: false,
                    requestedRect: targetRect,
                    frameRect,
                    targetToken,
                    targetPayload,
                    frameVersion,
                    imagePath,
                    checksum,
                    byteSize,
                    regions: frameRegions,
                    eligible: false,
                    eligibilityReasons: [focusRiskReason],
                    cleanupAction,
                    staleTimeoutMs,
                    sessionId: this._shellRasterSessionIdFromVersion(frameVersion),
                    focusRiskReason,
                    allowUnfocusedTarget,
                    requestDiagnostics,
                }),
            });
        }
        const eligibility = this._shellRasterFrameEligibility(targetPayload, targetRect, frameRect, rectTolerance);
        const pathValidation = multiRegionRequested
            ? this._validateShellRasterFrameRegions(frameRegions, targetRect)
            : this._validateShellRasterFramePath(imagePath, byteSize);
        const reasons = [...eligibility.reasons, ...pathValidation.reasons];
        if (reasons.length) {
            const cleanupAction = this._clearShellRasterFrame('invalid_frame');
            return this._presentationPayload({
                status: targetPayload ? 'presentation_degraded' : 'target_unavailable',
                action,
                targetToken,
                requestedRect: targetRect,
                appliedRect: null,
                standaloneMode,
                generatedAtUnixMs,
                generatedAtMonotonicUs,
                renderer: SHELL_RASTER_FRAME_RENDERER,
                degradeReasons: reasons,
                cleanupAction,
                detail: 'shell raster frame eligibility failed',
                shellRasterFrame: this._shellRasterFramePayload({
                    requestedAction: normalisedAction,
                    visible: false,
                    requestedRect: targetRect,
                    frameRect,
                    targetToken,
                    targetPayload,
                    frameVersion,
                    imagePath,
                    checksum,
                    byteSize,
                    regions: frameRegions,
                    eligible: false,
                    eligibilityReasons: reasons,
                    cleanupAction,
                    staleTimeoutMs,
                    sessionId: this._shellRasterSessionIdFromVersion(frameVersion),
                    allowUnfocusedTarget,
                    requestDiagnostics,
                }),
            });
        }

        const frameResult = multiRegionRequested
            ? this._showShellRasterFrameRegions({
                targetPayload,
                targetRect,
                frameRect,
                frameVersion,
                regions: frameRegions,
                staleTimeoutMs,
            })
            : this._showShellRasterFrame({
                targetPayload,
                targetRect,
                frameRect,
                frameVersion,
                imagePath,
                checksum,
                byteSize,
                staleTimeoutMs,
            });
        const degradeReasons = frameResult.visible ? [] : frameResult.reasons;
        return this._presentationPayload({
            status: frameResult.visible ? 'presentation_applied' : 'presentation_degraded',
            action,
            targetToken,
            requestedRect: targetRect,
            appliedRect: frameResult.visible ? frameRect : null,
            renderer: SHELL_RASTER_FRAME_RENDERER,
            placement: frameResult.visible,
            chromeFree: frameResult.visible,
            stacking: frameResult.visible,
            clickThrough: frameResult.visible,
            focusSafe: frameResult.visible,
            standaloneMode,
            generatedAtUnixMs,
            generatedAtMonotonicUs,
            degradeReasons,
            frameVersion,
            frameRect,
            frameDimensions: frameResult.frameDimensions,
            cleanupAction: frameResult.cleanupAction,
            detail: frameResult.visible ? '' : 'shell raster frame unavailable',
            shellRasterFrame: this._shellRasterFramePayload({
                requestedAction: normalisedAction,
                visible: frameResult.visible,
                requestedRect: targetRect,
                appliedRect: frameResult.visible ? frameRect : null,
                frameRect,
                targetToken,
                targetPayload,
                actorParent: frameResult.actorParent,
                frameVersion,
                imagePath,
                checksum,
                byteSize,
                regions: frameResult.regions || frameRegions,
                eligible: true,
                eligibilityReasons: degradeReasons,
                staleTimeoutMs,
                frameDimensions: frameResult.frameDimensions,
                cleanupAction: frameResult.cleanupAction,
                sessionId: frameResult.sessionId,
                allowUnfocusedTarget,
                requestDiagnostics,
                helperTiming: frameResult.timing,
                updateReason: frameResult.updateReason,
            }),
        });
    }

    _shellRasterFrameFocusRiskReason(targetPayload, allowUnfocusedTarget = false) {
        const overview = Main?.overview || null;
        if (overview) {
            if (overview.visible || overview._shown || overview._shownTransition || overview.animationInProgress) {
                return 'gnome_overview_active';
            }
        }
        if (!allowUnfocusedTarget && targetPayload && targetPayload.hasFocus === false) {
            return 'target_not_focused';
        }
        return '';
    }

    _shellRasterFrameEligibility(targetPayload, targetRect, frameRect, rectTolerance) {
        const reasons = [];
        if (!targetPayload) {
            reasons.push('target_unavailable');
            return { eligible: false, reasons };
        }
        if (!targetPayload.fullscreen) {
            reasons.push('target_not_fullscreen');
        }
        if (!targetPayload.showingOnWorkspace) {
            reasons.push('target_not_on_current_workspace');
        }
        if (targetPayload.minimized) {
            reasons.push('target_minimized');
        }
        if (!this._rectIsValid(targetPayload.contentRect)) {
            reasons.push('missing_target_content_rect');
        }
        if (!this._rectIsValid(targetPayload.monitorRect)) {
            reasons.push('missing_target_monitor_rect');
        }
        if (!this._rectIsValid(targetRect)) {
            reasons.push('invalid_target_rect');
        }
        if (!this._rectIsValid(frameRect)) {
            reasons.push('invalid_frame_rect');
        }
        if (
            this._rectIsValid(targetPayload.contentRect) &&
            this._rectIsValid(targetPayload.monitorRect) &&
            !this._rectsMatchWithinTolerance(targetPayload.contentRect, targetPayload.monitorRect, rectTolerance)
        ) {
            reasons.push('target_not_borderless_full_monitor');
        }
        if (
            this._rectIsValid(targetPayload.contentRect) &&
            this._rectIsValid(targetRect) &&
            !this._rectsMatchWithinTolerance(targetRect, targetPayload.contentRect, rectTolerance)
        ) {
            reasons.push('target_rect_mismatch');
        }
        if (
            this._rectIsValid(frameRect) &&
            this._rectIsValid(targetRect) &&
            !this._rectContains(targetRect, frameRect)
        ) {
            reasons.push('frame_rect_mismatch');
        }
        return {
            eligible: reasons.length === 0,
            reasons,
        };
    }

    _validateShellRasterFramePath(imagePath, byteSize) {
        const reasons = [];
        const path = String(imagePath || '').trim();
        if (!path || !GLib.path_is_absolute(path)) {
            reasons.push('invalid_path');
            return { ok: false, reasons, path: '' };
        }
        if (path.includes('/../') || path.endsWith('/..')) {
            reasons.push('path_traversal');
        }
        if (!path.toLowerCase().endsWith('.png')) {
            reasons.push('invalid_image_format');
        }
        const canonicalPath = GLib.canonicalize_filename(path, null);
        const allowed = this._shellRasterAllowedCacheDirs()
            .map(dir => GLib.canonicalize_filename(dir, null));
        if (!allowed.some(dir => canonicalPath === dir || canonicalPath.startsWith(`${dir}/`))) {
            reasons.push('path_outside_allowed_cache_dir');
        }
        const expectedBytes = Number(byteSize) || 0;
        if (expectedBytes <= 0) {
            reasons.push('invalid_byte_size');
        }
        if (expectedBytes > SHELL_RASTER_FRAME_MAX_BYTES) {
            reasons.push('file_too_large');
        }
        try {
            const file = Gio.File.new_for_path(canonicalPath);
            const info = file.query_info(
                'standard::type,standard::size,standard::content-type',
                Gio.FileQueryInfoFlags.NONE,
                null,
            );
            if (info.get_file_type() !== Gio.FileType.REGULAR) {
                reasons.push('not_regular_file');
            }
            const actualBytes = Number(info.get_size()) || 0;
            if (actualBytes <= 0) {
                reasons.push('file_missing');
            }
            if (actualBytes > SHELL_RASTER_FRAME_MAX_BYTES) {
                reasons.push('file_too_large');
            }
            if (expectedBytes > 0 && actualBytes !== expectedBytes) {
                reasons.push('byte_size_mismatch');
            }
            const contentType = String(info.get_content_type?.() || '').toLowerCase();
            if (contentType && contentType !== 'image/png') {
                reasons.push('invalid_image_format');
            }
        } catch (_error) {
            reasons.push('file_missing');
        }
        return {
            ok: reasons.length === 0,
            reasons: [...new Set(reasons)],
            path: canonicalPath,
        };
    }

    _shellRasterFrameRegionsFromPayload({ regions, targetToken, targetRect }) {
        const parsed = [];
        for (const entry of regions || []) {
            if (!entry || typeof entry !== 'object' || Array.isArray(entry)) {
                continue;
            }
            const regionId = this._requestString(entry, 'region_id', 'regionId');
            const frameRect = this._requestRect(entry, 'frame_rect', 'frameRect');
            const imagePath = this._requestString(entry, 'image_path', 'imagePath');
            const checksum = this._requestString(entry, 'checksum');
            const byteSize = this._requestInt(entry, 0, 'byte_size', 'byteSize');
            parsed.push({
                regionId,
                targetToken: this._requestString(entry, 'target_token', 'targetToken') || targetToken,
                targetRect: this._requestRect(entry, 'target_rect', 'targetRect') || targetRect,
                frameRect,
                frameVersion: this._requestString(entry, 'frame_version', 'frameVersion'),
                imagePath,
                checksum,
                byteSize,
                diagnostics: this._requestObject(entry, 'diagnostics'),
            });
        }
        return parsed.filter(region => region.regionId && this._rectIsValid(region.frameRect));
    }

    _validateShellRasterFrameRegions(regions, targetRect) {
        const reasons = [];
        if (!Array.isArray(regions) || regions.length <= 0) {
            return { ok: false, reasons: ['missing_regions'] };
        }
        const seenRegionIds = new Set();
        for (const region of regions) {
            if (!region.regionId) {
                reasons.push('invalid_region_id');
            }
            if (seenRegionIds.has(region.regionId)) {
                reasons.push('duplicate_region_id');
            }
            seenRegionIds.add(region.regionId);
            if (!this._rectIsValid(region.frameRect)) {
                reasons.push('invalid_region_frame_rect');
            } else if (this._rectIsValid(targetRect) && !this._rectContains(targetRect, region.frameRect)) {
                reasons.push('region_frame_rect_mismatch');
            }
            const pathValidation = this._validateShellRasterFramePath(region.imagePath, region.byteSize);
            reasons.push(...pathValidation.reasons.map(reason => `region_${reason}`));
        }
        return {
            ok: reasons.length === 0,
            reasons: [...new Set(reasons)],
        };
    }

    _shellRasterAllowedCacheDirs() {
        const dirs = [];
        const runtimeDir = String(GLib.getenv('XDG_RUNTIME_DIR') || GLib.get_user_runtime_dir?.() || '').trim();
        if (runtimeDir) {
            dirs.push(GLib.build_filenamev([runtimeDir, 'EDMCModernOverlay', 'shell-raster']));
        }
        dirs.push(GLib.build_filenamev([
            GLib.get_tmp_dir(),
            `EDMCModernOverlay-shell-raster-${GLib.get_user_name()}`,
        ]));
        return dirs;
    }

    _showShellRasterFrame({
        targetPayload,
        targetRect,
        frameRect,
        frameVersion,
        imagePath,
        checksum,
        byteSize,
        staleTimeoutMs,
    }) {
        const totalStartedUs = GLib.get_monotonic_time();
        const sessionId = this._shellRasterSessionIdFromVersion(frameVersion);
        const targetActor = this._targetWindowActorForToken(targetPayload?.targetToken || '');
        if (!targetActor || typeof targetActor.add_child !== 'function') {
            const cleanupAction = this._clearShellRasterFrame('missing_target_window_actor');
            return {
                visible: false,
                actorParent: SHELL_RASTER_FRAME_PARENT,
                frameDimensions: null,
                cleanupAction,
                reasons: ['target_window_actor_unavailable'],
                timing: this._shellRasterHelperTiming(totalStartedUs),
            };
        }
        const reusableFrame = this._reuseShellRasterFrameIfMatching({
            targetActor,
            targetPayload,
            targetRect,
            frameRect,
            frameVersion,
            imagePath,
            checksum,
            byteSize,
            staleTimeoutMs,
            startedUs: totalStartedUs,
        });
        if (reusableFrame) {
            return reusableFrame;
        }
        const regionsCleanupAction = this._clearShellRasterRegionActors('replace_regions_with_single');
        const cleanupReason = this._shellRasterFrame?.sessionId &&
            sessionId &&
            this._shellRasterFrame.sessionId !== sessionId
            ? 'session_generation_mismatch'
            : 'replace_existing';
        const cleanupAction = this._clearShellRasterFrame(cleanupReason) || regionsCleanupAction;
        let textureActor = null;
        let dimensions = null;
        let decodeMs = 0;
        try {
            const decodeStartedUs = GLib.get_monotonic_time();
            const loaded = this._loadShellRasterTextureActor(imagePath);
            decodeMs = this._elapsedMs(decodeStartedUs);
            textureActor = loaded.actor;
            dimensions = loaded.dimensions;
            if (dimensions.width > frameRect.width || dimensions.height > frameRect.height) {
                textureActor.destroy?.();
                return {
                    visible: false,
                    actorParent: SHELL_RASTER_FRAME_PARENT,
                    frameDimensions: dimensions,
                    cleanupAction,
                    reasons: ['frame_dimensions_exceed_rect'],
                    timing: this._shellRasterHelperTiming(totalStartedUs, { decodeMs }),
                };
            }
        } catch (_error) {
            decodeMs = this._elapsedMs(totalStartedUs);
            return {
                visible: false,
                actorParent: SHELL_RASTER_FRAME_PARENT,
                frameDimensions: null,
                cleanupAction,
                reasons: ['decode_load_failed'],
                timing: this._shellRasterHelperTiming(totalStartedUs, { decodeMs }),
            };
        }

        const localX = frameRect.x - targetRect.x;
        const localY = frameRect.y - targetRect.y;
        const applyStartedUs = GLib.get_monotonic_time();
        let applyMs = 0;
        textureActor.set_reactive?.(false);
        textureActor.set_position(localX, localY);
        textureActor.set_size(frameRect.width, frameRect.height);
        try {
            targetActor.add_child(textureActor);
        } catch (_error) {
            applyMs = this._elapsedMs(applyStartedUs);
            textureActor.destroy?.();
            return {
                visible: false,
                actorParent: SHELL_RASTER_FRAME_PARENT,
                frameDimensions: dimensions,
                cleanupAction,
                reasons: ['texture_apply_failed'],
                timing: this._shellRasterHelperTiming(totalStartedUs, { decodeMs, applyMs }),
            };
        }
        textureActor.show?.();
        textureActor.raise_top?.();
        applyMs = this._elapsedMs(applyStartedUs);
        this._shellRasterFrame = {
            actor: textureActor,
            targetToken: targetPayload.targetToken,
            targetRect,
            frameRect,
            frameVersion,
            imagePath,
            checksum,
            byteSize,
            sessionId,
            actorParent: SHELL_RASTER_FRAME_PARENT,
            frameDimensions: dimensions,
        };
        this._refreshShellRasterFrameTimeout(staleTimeoutMs);
        return {
            visible: true,
            actorParent: SHELL_RASTER_FRAME_PARENT,
            frameDimensions: dimensions,
            cleanupAction,
            sessionId,
            updateReason: 'decoded_new_frame',
            reasons: [],
            timing: this._shellRasterHelperTiming(totalStartedUs, {
                decodeMs,
                applyMs,
                updateReason: 'decoded_new_frame',
            }),
        };
    }

    _showShellRasterFrameRegions({
        targetPayload,
        targetRect,
        frameRect,
        frameVersion,
        regions,
        staleTimeoutMs,
    }) {
        const totalStartedUs = GLib.get_monotonic_time();
        const sessionId = this._shellRasterSessionIdFromVersion(frameVersion);
        const targetActor = this._targetWindowActorForToken(targetPayload?.targetToken || '');
        if (!targetActor || typeof targetActor.add_child !== 'function') {
            const cleanupAction = this._clearShellRasterFrame('missing_target_window_actor');
            return {
                visible: false,
                actorParent: SHELL_RASTER_FRAME_PARENT,
                appliedRect: null,
                frameDimensions: null,
                cleanupAction,
                reasons: ['target_window_actor_unavailable'],
                timing: this._shellRasterHelperTiming(totalStartedUs),
                regions: [],
            };
        }

        this._clearSingleShellRasterFrame('replace_single_with_regions');
        const incomingIds = new Set(regions.map(region => region.regionId));
        const regionResults = [];
        let totalDecodeMs = 0;
        let totalApplyMs = 0;
        let decodedCount = 0;
        let reusedCount = 0;
        let cleanupAction = '';

        for (const region of regions) {
            const regionStartedUs = GLib.get_monotonic_time();
            const reusable = this._reuseShellRasterRegionIfMatching({
                targetActor,
                targetPayload,
                targetRect,
                region,
                staleTimeoutMs,
                startedUs: regionStartedUs,
            });
            if (reusable) {
                reusedCount += 1;
                totalApplyMs += Number(reusable.timing?.helper_apply_ms || 0);
                regionResults.push(reusable.regionPayload);
                continue;
            }

            let textureActor = null;
            let dimensions = null;
            let decodeMs = 0;
            try {
                const decodeStartedUs = GLib.get_monotonic_time();
                const loaded = this._loadShellRasterTextureActor(region.imagePath);
                decodeMs = this._elapsedMs(decodeStartedUs);
                textureActor = loaded.actor;
                dimensions = loaded.dimensions;
                if (dimensions.width > region.frameRect.width || dimensions.height > region.frameRect.height) {
                    textureActor.destroy?.();
                    this._clearShellRasterFrame('region_dimensions_exceed_rect');
                    return {
                        visible: false,
                        actorParent: SHELL_RASTER_FRAME_PARENT,
                        appliedRect: null,
                        frameDimensions: null,
                        cleanupAction: 'region_dimensions_exceed_rect',
                        reasons: ['frame_dimensions_exceed_rect'],
                        timing: this._shellRasterHelperTiming(totalStartedUs, { decodeMs: totalDecodeMs + decodeMs }),
                        regions: regionResults,
                    };
                }
            } catch (_error) {
                this._clearShellRasterFrame('region_decode_load_failed');
                return {
                    visible: false,
                    actorParent: SHELL_RASTER_FRAME_PARENT,
                    appliedRect: null,
                    frameDimensions: null,
                    cleanupAction: 'region_decode_load_failed',
                    reasons: ['decode_load_failed'],
                    timing: this._shellRasterHelperTiming(totalStartedUs, { decodeMs: totalDecodeMs }),
                    regions: regionResults,
                };
            }

            const localX = region.frameRect.x - targetRect.x;
            const localY = region.frameRect.y - targetRect.y;
            const applyStartedUs = GLib.get_monotonic_time();
            let applyMs = 0;
            textureActor.set_reactive?.(false);
            textureActor.set_position(localX, localY);
            textureActor.set_size(region.frameRect.width, region.frameRect.height);
            try {
                this._destroyShellRasterRegion(region.regionId, 'replace_region');
                targetActor.add_child(textureActor);
            } catch (_error) {
                applyMs = this._elapsedMs(applyStartedUs);
                textureActor.destroy?.();
                this._clearShellRasterFrame('region_texture_apply_failed');
                return {
                    visible: false,
                    actorParent: SHELL_RASTER_FRAME_PARENT,
                    appliedRect: null,
                    frameDimensions: null,
                    cleanupAction: 'region_texture_apply_failed',
                    reasons: ['texture_apply_failed'],
                    timing: this._shellRasterHelperTiming(totalStartedUs, {
                        decodeMs: totalDecodeMs + decodeMs,
                        applyMs: totalApplyMs + applyMs,
                    }),
                    regions: regionResults,
                };
            }
            textureActor.show?.();
            textureActor.raise_top?.();
            applyMs = this._elapsedMs(applyStartedUs);
            decodedCount += 1;
            totalDecodeMs += decodeMs;
            totalApplyMs += applyMs;
            const record = {
                actor: textureActor,
                regionId: region.regionId,
                targetToken: targetPayload.targetToken,
                targetRect,
                frameRect: region.frameRect,
                frameVersion: region.frameVersion,
                imagePath: region.imagePath,
                checksum: region.checksum,
                byteSize: region.byteSize,
                sessionId,
                actorParent: SHELL_RASTER_FRAME_PARENT,
                frameDimensions: dimensions,
            };
            this._shellRasterRegions.set(region.regionId, record);
            regionResults.push(this._shellRasterRegionStatusPayload(region, {
                actor_visible: true,
                actor_parent: SHELL_RASTER_FRAME_PARENT,
                frame_dimensions: dimensions,
                session_id: sessionId,
                update_reason: 'decoded_new_region',
                diagnostics: this._shellRasterHelperTiming(regionStartedUs, {
                    decodeMs,
                    applyMs,
                    updateReason: 'decoded_new_region',
                }),
            }));
        }

        for (const regionId of [...this._shellRasterRegions.keys()]) {
            if (!incomingIds.has(regionId)) {
                cleanupAction = this._destroyShellRasterRegion(regionId, 'remove_stale_region') || cleanupAction;
            }
        }
        this._refreshShellRasterFrameTimeout(staleTimeoutMs);
        return {
            visible: true,
            actorParent: SHELL_RASTER_FRAME_PARENT,
            appliedRect: frameRect,
            frameDimensions: { x: 0, y: 0, width: frameRect.width, height: frameRect.height },
            cleanupAction,
            sessionId,
            updateReason: 'multi_region_update',
            reasons: [],
            regions: regionResults,
            timing: this._shellRasterHelperTiming(totalStartedUs, {
                decodeMs: totalDecodeMs,
                applyMs: totalApplyMs,
                reusedFrame: reusedCount > 0 && decodedCount === 0,
                decodeSkipped: decodedCount === 0,
                updateReason: decodedCount === 0 ? 'reused_existing_regions' : 'decoded_changed_regions',
            }),
        };
    }

    _reuseShellRasterFrameIfMatching({
        targetActor,
        targetPayload,
        targetRect,
        frameRect,
        frameVersion,
        imagePath,
        checksum,
        byteSize,
        staleTimeoutMs,
        startedUs,
    }) {
        const frame = this._shellRasterFrame;
        if (!frame?.actor) {
            return null;
        }
        if (!this._shellRasterFrameIdentityMatches(frame, {
            targetToken: targetPayload?.targetToken || '',
            targetRect,
            frameRect,
            frameVersion,
            imagePath,
            checksum,
            byteSize,
        })) {
            return null;
        }
        if (typeof frame.actor.get_parent === 'function' && frame.actor.get_parent() !== targetActor) {
            return null;
        }

        const applyStartedUs = GLib.get_monotonic_time();
        frame.actor.show?.();
        frame.actor.raise_top?.();
        this._refreshShellRasterFrameTimeout(staleTimeoutMs);
        return {
            visible: true,
            actorParent: frame.actorParent || SHELL_RASTER_FRAME_PARENT,
            frameDimensions: frame.frameDimensions,
            cleanupAction: '',
            sessionId: frame.sessionId,
            updateReason: 'reused_existing_frame',
            reasons: [],
            timing: this._shellRasterHelperTiming(startedUs, {
                decodeMs: 0,
                applyMs: this._elapsedMs(applyStartedUs),
                reusedFrame: true,
                decodeSkipped: true,
                updateReason: 'reused_existing_frame',
            }),
        };
    }

    _reuseShellRasterRegionIfMatching({
        targetActor,
        targetPayload,
        targetRect,
        region,
        startedUs,
    }) {
        const frame = this._shellRasterRegions.get(region.regionId);
        if (!frame?.actor) {
            return null;
        }
        if (!this._shellRasterFrameIdentityMatches(frame, {
            targetToken: targetPayload?.targetToken || '',
            targetRect,
            frameRect: region.frameRect,
            frameVersion: region.frameVersion,
            imagePath: region.imagePath,
            checksum: region.checksum,
            byteSize: region.byteSize,
        })) {
            return null;
        }
        if (typeof frame.actor.get_parent === 'function' && frame.actor.get_parent() !== targetActor) {
            return null;
        }

        const applyStartedUs = GLib.get_monotonic_time();
        frame.actor.show?.();
        frame.actor.raise_top?.();
        const timing = this._shellRasterHelperTiming(startedUs, {
            decodeMs: 0,
            applyMs: this._elapsedMs(applyStartedUs),
            reusedFrame: true,
            decodeSkipped: true,
            updateReason: 'reused_existing_region',
        });
        return {
            timing,
            regionPayload: this._shellRasterRegionStatusPayload(region, {
                actor_visible: true,
                actor_parent: frame.actorParent || SHELL_RASTER_FRAME_PARENT,
                frame_dimensions: frame.frameDimensions,
                session_id: frame.sessionId,
                update_reason: 'reused_existing_region',
                diagnostics: timing,
            }),
        };
    }

    _shellRasterFrameIdentityMatches(frame, {
        targetToken,
        targetRect,
        frameRect,
        frameVersion,
        imagePath,
        checksum,
        byteSize,
    }) {
        return String(frame.frameVersion || '') === String(frameVersion || '') &&
            String(frame.checksum || '') === String(checksum || '') &&
            String(frame.imagePath || '') === String(imagePath || '') &&
            Number(frame.byteSize || 0) === Number(byteSize || 0) &&
            String(frame.targetToken || '') === String(targetToken || '') &&
            this._rectsMatchWithinTolerance(frame.targetRect, targetRect, 0) &&
            this._rectsMatchWithinTolerance(frame.frameRect, frameRect, 0);
    }

    _shellRasterSessionIdFromVersion(frameVersion) {
        const parts = String(frameVersion || '').split(':').map(part => part.trim()).filter(part => part);
        return parts.length >= 3 ? parts[1] : '';
    }

    _loadShellRasterTextureActor(imagePath) {
        const pixbuf = GdkPixbuf.Pixbuf.new_from_file(imagePath);
        const width = Number(pixbuf.get_width?.() || 0);
        const height = Number(pixbuf.get_height?.() || 0);
        const hasAlpha = Boolean(pixbuf.get_has_alpha?.());
        const channels = Number(pixbuf.get_n_channels?.() || 0);
        if (width <= 0 || height <= 0 || !hasAlpha || channels !== 4) {
            throw new Error('PNG frame must be RGBA');
        }
        const image = new Clutter.Image();
        image.set_data(
            pixbuf.get_pixels(),
            Cogl.PixelFormat.RGBA_8888,
            width,
            height,
            Number(pixbuf.get_rowstride?.() || width * 4),
        );
        const actor = new Clutter.Actor({
            reactive: false,
            visible: true,
        });
        actor.set_content(image);
        return {
            actor,
            dimensions: { x: 0, y: 0, width, height },
        };
    }

    _shellRasterFramePayload({
        requestedAction,
        visible,
        requestedRect = null,
        appliedRect = null,
        frameRect = null,
        targetToken = '',
        targetPayload = null,
        actorParent = '',
        frameVersion = '',
        imagePath = '',
        checksum = '',
        byteSize = 0,
        regions = [],
        eligible = true,
        eligibilityReasons = [],
        cleanupAction = '',
        staleTimeoutMs = SHELL_RASTER_FRAME_TIMEOUT_MS_DEFAULT,
        frameDimensions = null,
        sessionId = '',
        focusRiskReason = '',
        allowUnfocusedTarget = false,
        requestDiagnostics = null,
        helperTiming = null,
        updateReason = '',
    }) {
        const framePayload = {
            schema: 1,
            requested: Boolean(requestedAction),
            action: requestedAction,
            actor_visible: Boolean(visible),
            target_token: targetToken,
            target_monitor: targetPayload?.monitor ?? null,
            target_monitor_rect: targetPayload?.monitorRect || null,
            target_rect: requestedRect,
            frame_rect: frameRect,
            applied_actor_bounds: appliedRect,
            actor_parent: actorParent || this._shellRasterFrame?.actorParent || '',
            frame_version: frameVersion,
            frame_dimensions: frameDimensions,
            image_path: imagePath,
            checksum,
            byte_size: byteSize,
            regions: Array.isArray(regions) ? regions.map(region => this._shellRasterRegionStatusPayload(region)) : [],
            region_count: Array.isArray(regions) ? regions.length : 0,
            session_id: sessionId || this._shellRasterFrame?.sessionId || '',
            eligible,
            eligibility_reasons: eligibilityReasons,
            stale_timeout_ms: staleTimeoutMs,
            cleanup_action: cleanupAction,
            focus_risk_reason: focusRiskReason,
            allow_unfocused_target: Boolean(allowUnfocusedTarget),
            update_reason: updateReason,
        };
        const diagnostics = this._shellRasterFrameDiagnostics(requestDiagnostics, helperTiming);
        if (diagnostics) {
            framePayload.diagnostics = diagnostics;
        }
        return framePayload;
    }

    _shellRasterRegionStatusPayload(region, extra = {}) {
        return {
            region_id: String(region?.regionId || region?.region_id || ''),
            target_token: String(region?.targetToken || region?.target_token || ''),
            target_rect: region?.targetRect || region?.target_rect || null,
            frame_rect: region?.frameRect || region?.frame_rect || null,
            frame_version: String(region?.frameVersion || region?.frame_version || ''),
            frame_dimensions: region?.frameDimensions || region?.frame_dimensions || null,
            image_path: String(region?.imagePath || region?.image_path || ''),
            checksum: String(region?.checksum || ''),
            byte_size: Number(region?.byteSize || region?.byte_size || 0) || 0,
            update_reason: String(region?.updateReason || region?.update_reason || ''),
            ...extra,
        };
    }

    _shellRasterFrameDiagnostics(requestDiagnostics, helperTiming) {
        if (!requestDiagnostics && !helperTiming) {
            return null;
        }
        return {
            schema: 1,
            request: requestDiagnostics || null,
            helper: helperTiming || null,
        };
    }

    _shellRasterHelperTiming(
        startedUs,
        {
            decodeMs = 0,
            applyMs = 0,
            reusedFrame = false,
            decodeSkipped = false,
            updateReason = '',
        } = {},
    ) {
        return {
            helper_decode_ms: Number(decodeMs) || 0,
            helper_apply_ms: Number(applyMs) || 0,
            helper_total_ms: this._elapsedMs(startedUs),
            helper_reused_frame: Boolean(reusedFrame),
            helper_decode_skipped: Boolean(decodeSkipped),
            helper_update_reason: updateReason,
        };
    }

    _elapsedMs(startedUs) {
        const started = Number(startedUs) || 0;
        if (started <= 0) {
            return 0;
        }
        return Math.round(((GLib.get_monotonic_time() - started) / 1000) * 1000) / 1000;
    }

    _refreshShellRasterFrameTimeout(timeoutMs = SHELL_RASTER_FRAME_TIMEOUT_MS_DEFAULT) {
        if (this._shellRasterFrameTimeoutId) {
            GLib.source_remove(this._shellRasterFrameTimeoutId);
            this._shellRasterFrameTimeoutId = 0;
        }
        this._shellRasterFrameTimeoutId = GLib.timeout_add(
            GLib.PRIORITY_DEFAULT,
            Math.max(1000, Number(timeoutMs) || SHELL_RASTER_FRAME_TIMEOUT_MS_DEFAULT),
            () => {
                this._clearShellRasterFrame('stale_timeout');
                return GLib.SOURCE_REMOVE;
            },
        );
    }

    _clearShellRasterFrame(reason = 'clear') {
        const hadActor = Boolean(this._shellRasterFrame?.actor);
        const hadRegions = Boolean(this._shellRasterRegions?.size);
        const frame = this._shellRasterFrame;
        if (this._shellRasterFrameTimeoutId) {
            GLib.source_remove(this._shellRasterFrameTimeoutId);
            this._shellRasterFrameTimeoutId = 0;
        }
        this._shellRasterFrame = null;
        this._clearShellRasterRegionActors(reason);
        try {
            const parent = frame?.actor?.get_parent?.();
            if (parent && typeof parent.remove_child === 'function') {
                parent.remove_child(frame.actor);
            }
        } catch (_error) {
            // Best-effort cleanup only; diagnostics report the requested cleanup reason.
        }
        try {
            frame?.actor?.destroy?.();
        } catch (_error) {
            // Best-effort cleanup only; diagnostics report the requested cleanup reason.
        }
        return hadActor || hadRegions ? reason : '';
    }

    _clearSingleShellRasterFrame(reason = 'clear_single') {
        const frame = this._shellRasterFrame;
        if (!frame?.actor) {
            this._shellRasterFrame = null;
            return '';
        }
        this._shellRasterFrame = null;
        try {
            const parent = frame.actor.get_parent?.();
            if (parent && typeof parent.remove_child === 'function') {
                parent.remove_child(frame.actor);
            }
        } catch (_error) {
            // Best-effort cleanup only; diagnostics report the requested cleanup reason.
        }
        try {
            frame.actor.destroy?.();
        } catch (_error) {
            // Best-effort cleanup only; diagnostics report the requested cleanup reason.
        }
        return reason;
    }

    _clearShellRasterRegionActors(reason = 'clear_regions') {
        let cleanupAction = '';
        for (const regionId of [...(this._shellRasterRegions?.keys?.() || [])]) {
            cleanupAction = this._destroyShellRasterRegion(regionId, reason) || cleanupAction;
        }
        return cleanupAction;
    }

    _destroyShellRasterRegion(regionId, reason = 'destroy_region') {
        const frame = this._shellRasterRegions?.get(regionId);
        if (!frame?.actor) {
            this._shellRasterRegions?.delete?.(regionId);
            return '';
        }
        this._shellRasterRegions.delete(regionId);
        try {
            const parent = frame.actor.get_parent?.();
            if (parent && typeof parent.remove_child === 'function') {
                parent.remove_child(frame.actor);
            }
        } catch (_error) {
            // Best-effort cleanup only; diagnostics report the requested cleanup reason.
        }
        try {
            frame.actor.destroy?.();
        } catch (_error) {
            // Best-effort cleanup only; diagnostics report the requested cleanup reason.
        }
        return reason;
    }

    _connectShellRasterOverviewSignals() {
        const overview = Main?.overview || null;
        if (!overview || typeof overview.connect !== 'function') {
            return;
        }
        for (const signalName of ['showing', 'shown', 'hiding']) {
            try {
                const signalId = overview.connect(signalName, () => {
                    this._clearShellRasterFrame('gnome_overview_active');
                });
                this._shellRasterOverviewSignalIds.push([overview, signalId]);
            } catch (_error) {
                // Some GNOME Shell versions may not expose every overview signal.
            }
        }
    }

    _disconnectShellRasterOverviewSignals() {
        for (const [overview, signalId] of this._shellRasterOverviewSignalIds) {
            try {
                overview.disconnect(signalId);
            } catch (_error) {
                // Best-effort cleanup on helper disable.
            }
        }
        this._shellRasterOverviewSignalIds = [];
    }

    _rectContains(outerRect, innerRect) {
        if (!this._rectIsValid(outerRect) || !this._rectIsValid(innerRect)) {
            return false;
        }
        return innerRect.x >= outerRect.x &&
            innerRect.y >= outerRect.y &&
            innerRect.x + innerRect.width <= outerRect.x + outerRect.width &&
            innerRect.y + innerRect.height <= outerRect.y + outerRect.height;
    }

    _handleShellActorProof({
        action,
        targetToken,
        requestedRect,
        standaloneMode,
        generatedAtUnixMs,
        generatedAtMonotonicUs,
        proofAction,
        rectTolerance,
    }) {
        const normalisedAction = String(proofAction || 'show').trim().toLowerCase();
        if (normalisedAction === 'clear') {
            const cleanupAction = this._clearShellActorProof('explicit_clear');
            return this._presentationPayload({
                status: 'shell_actor_proof_cleared',
                action,
                targetToken,
                requestedRect,
                standaloneMode,
                generatedAtUnixMs,
                generatedAtMonotonicUs,
                shellActorProof: this._shellActorProofPayload({
                    requestedAction: normalisedAction,
                    visible: false,
                    requestedRect,
                    targetToken,
                    cleanupAction,
                }),
            });
        }
        if (normalisedAction === 'diagnose_groups') {
            return this._presentationPayload({
                status: 'shell_actor_group_diagnostics',
                action,
                targetToken,
                requestedRect,
                standaloneMode,
                generatedAtUnixMs,
                generatedAtMonotonicUs,
                renderer: 'gnome_shell_actor_proof',
                shellActorProof: this._shellActorProofPayload({
                    requestedAction: normalisedAction,
                    visible: Boolean(this._shellActorProof?.actor),
                    requestedRect,
                    targetToken,
                    groupDiagnostics: this._shellActorGroupDiagnostics(targetToken),
                }),
            });
        }
        if (normalisedAction !== 'show') {
            return this._presentationPayload({
                status: 'malformed_payload',
                action: 'degrade',
                targetToken,
                requestedRect,
                standaloneMode,
                generatedAtUnixMs,
                generatedAtMonotonicUs,
                degradeReasons: ['unsupported_shell_actor_proof_action'],
                detail: `unsupported shell actor proof action=${normalisedAction}`,
                shellActorProof: this._shellActorProofPayload({
                    requestedAction: normalisedAction,
                    visible: Boolean(this._shellActorProof?.actor),
                    requestedRect,
                    targetToken,
                    eligible: false,
                    eligibilityReasons: ['unsupported_shell_actor_proof_action'],
                }),
            });
        }

        const windows = this._enumerateWindowEntries();
        const targetEntry = windows.find(entry => entry.payload.targetToken === targetToken);
        const targetPayload = targetEntry?.payload || null;
        const eligibility = this._shellActorProofEligibility(targetPayload, requestedRect, rectTolerance);
        if (!eligibility.eligible) {
            const cleanupAction = this._clearShellActorProof('ineligible_target');
            return this._presentationPayload({
                status: targetPayload ? 'shell_actor_proof_ineligible' : 'target_unavailable',
                action,
                targetToken,
                requestedRect,
                standaloneMode,
                generatedAtUnixMs,
                generatedAtMonotonicUs,
                degradeReasons: eligibility.reasons,
                detail: 'shell actor proof eligibility failed',
                shellActorProof: this._shellActorProofPayload({
                    requestedAction: normalisedAction,
                    visible: false,
                    requestedRect,
                    targetToken,
                    targetPayload,
                    eligible: false,
                    eligibilityReasons: eligibility.reasons,
                    cleanupAction,
                }),
            });
        }

        const proofResult = this._showShellActorProof(targetPayload, requestedRect);
        const status = proofResult.visible ? 'shell_actor_proof_visible' : 'shell_actor_proof_degraded';
        return this._presentationPayload({
            status,
            action,
            targetToken,
            requestedRect,
            appliedRect: proofResult.appliedRect,
            renderer: 'gnome_shell_actor_proof',
            placement: proofResult.visible,
            chromeFree: proofResult.visible,
            stacking: proofResult.visible,
            clickThrough: proofResult.visible,
            focusSafe: proofResult.visible,
            standaloneMode,
            generatedAtUnixMs,
            generatedAtMonotonicUs,
            degradeReasons: proofResult.visible ? [] : ['shell_actor_proof_unavailable'],
            detail: proofResult.visible ? '' : 'shell actor proof unavailable',
            shellActorProof: this._shellActorProofPayload({
                requestedAction: normalisedAction,
                visible: proofResult.visible,
                requestedRect,
                targetToken,
                targetPayload,
                appliedRect: proofResult.appliedRect,
                actorParent: proofResult.actorParent,
                eligible: true,
                staleTimeoutSeconds: SHELL_ACTOR_PROOF_TIMEOUT_MS / 1000,
            }),
        });
    }

    _shellActorProofEligibility(targetPayload, requestedRect, rectTolerance) {
        const reasons = [];
        if (!targetPayload) {
            reasons.push('target_unavailable');
            return { eligible: false, reasons };
        }
        if (!targetPayload.fullscreen) {
            reasons.push('target_not_fullscreen');
        }
        if (!targetPayload.showingOnWorkspace) {
            reasons.push('target_not_on_current_workspace');
        }
        if (targetPayload.minimized) {
            reasons.push('target_minimized');
        }
        if (!this._rectIsValid(targetPayload.contentRect)) {
            reasons.push('missing_target_content_rect');
        }
        if (!this._rectIsValid(targetPayload.monitorRect)) {
            reasons.push('missing_target_monitor_rect');
        }
        if (!this._rectIsValid(requestedRect)) {
            reasons.push('invalid_requested_rect');
        }
        if (
            this._rectIsValid(targetPayload.contentRect) &&
            this._rectIsValid(targetPayload.monitorRect) &&
            !this._rectsMatchWithinTolerance(targetPayload.contentRect, targetPayload.monitorRect, rectTolerance)
        ) {
            reasons.push('target_content_rect_not_monitor_bounds');
        }
        if (
            this._rectIsValid(targetPayload.contentRect) &&
            this._rectIsValid(requestedRect) &&
            !this._rectsMatchWithinTolerance(requestedRect, targetPayload.contentRect, rectTolerance)
        ) {
            reasons.push('requested_rect_not_target_content_rect');
        }
        return {
            eligible: reasons.length === 0,
            reasons,
        };
    }

    _showShellActorProof(targetPayload, requestedRect) {
        const parent = this._shellActorProofParent(targetPayload);
        if (!parent.container) {
            this._clearShellActorProof('missing_actor_parent');
            return {
                visible: false,
                appliedRect: null,
                actorParent: parent.name,
            };
        }
        this._clearShellActorProof('replace_existing');

        const actor = new St.Widget({
            reactive: false,
            visible: true,
            style_class: 'edmc-shell-actor-proof',
            style: 'background-color: rgba(0, 0, 0, 0);',
        });
        actor.set_reactive?.(false);
        actor.set_position(requestedRect.x, requestedRect.y);
        actor.set_size(requestedRect.width, requestedRect.height);

        const outline = new St.Widget({
            reactive: false,
            visible: true,
            style_class: 'edmc-shell-actor-proof-outline',
            style: 'border: 3px solid rgba(0, 255, 180, 0.95); background-color: rgba(0, 0, 0, 0);',
        });
        outline.set_reactive?.(false);
        outline.set_position(0, 0);
        outline.set_size(requestedRect.width, requestedRect.height);

        const label = new St.Label({
            reactive: false,
            visible: true,
            text: 'EDMC Shell Proof',
            style_class: 'edmc-shell-actor-proof-label',
            style: 'background-color: rgba(0, 0, 0, 0.45); color: #00ffb4; padding: 6px 10px; font-weight: bold;',
        });
        label.set_reactive?.(false);
        label.set_position(16, 16);

        actor.add_child(outline);
        actor.add_child(label);
        const attached = this._addShellActorProofToParent(actor, parent);
        if (!attached) {
            actor.destroy?.();
            return {
                visible: false,
                appliedRect: null,
                actorParent: parent.name,
            };
        }
        actor.set_position(requestedRect.x, requestedRect.y);
        actor.set_size(requestedRect.width, requestedRect.height);
        actor.show?.();
        actor.raise_top?.();

        this._shellActorProof = {
            actor,
            targetToken: targetPayload.targetToken,
            requestedRect,
            actorParent: parent.name,
            actorParentMode: parent.mode,
        };
        this._refreshShellActorProofTimeout();
        return {
            visible: true,
            appliedRect: this._shellActorBounds(actor),
            actorParent: parent.name,
        };
    }

    _shellActorProofParent(targetPayload = null) {
        const targetActor = this._targetWindowActorForToken(targetPayload?.targetToken || '');
        return {
            container: targetActor,
            mode: 'target_window_actor_child',
            name: SHELL_ACTOR_PROOF_PARENT,
        };
    }

    _addShellActorProofToParent(actor, parent) {
        if (
            parent.mode === 'target_window_actor_child' &&
            typeof parent.container?.add_child === 'function'
        ) {
            try {
                parent.container.add_child(actor);
                return true;
            } catch (_error) {
                return false;
            }
        }
        return false;
    }

    _targetWindowActorForToken(targetToken = '') {
        if (!targetToken) {
            return null;
        }
        const actors = global.get_window_actors?.() || [];
        for (const actor of actors) {
            const window = this._metaWindowForActor(actor);
            if (window && this._targetToken(window) === targetToken) {
                return actor;
            }
        }
        return null;
    }

    _shellActorGroupDiagnostics(targetToken = '') {
        const uiGroup = this._uiGroupActor();
        return {
            schema: 1,
            target_token: targetToken,
            known_groups: SHELL_ACTOR_GROUP_DIAGNOSTIC_NAMES,
            child_limit: SHELL_ACTOR_GROUP_DIAGNOSTIC_CHILD_LIMIT,
            groups: SHELL_ACTOR_GROUP_DIAGNOSTIC_NAMES.map(name => this._shellActorGroupDiagnostic(
                name,
                {
                    targetToken,
                    includeWindowDetails: name === 'global.window_group',
                },
            )),
            stage_child_order: this._shellActorChildOrder('global.stage', { targetToken }),
            ui_group_child_order: this._actorChildOrder(
                'Main.uiGroup',
                uiGroup,
                { targetToken, includeWindowDetails: true },
            ),
            window_group_child_order: this._shellActorChildOrder(
                'global.window_group',
                { targetToken, includeWindowDetails: true },
            ),
            proof_actor: this._shellActorProofDiagnostic(),
            target_window_actor: this._targetWindowActorDiagnostic(targetToken),
        };
    }

    _shellActorGroupDiagnostic(name, options = {}) {
        const actor = this._globalActorByName(name);
        if (!actor) {
            return {
                name,
                available: false,
                actor_type: '',
                parent: '',
                parent_index: null,
                visible: null,
                mapped: null,
                reactive: null,
                bounds: null,
                child_count: 0,
                children: [],
                children_truncated: false,
            };
        }

        const children = this._actorChildren(actor);
        const parent = this._actorParent(actor);
        return {
            name,
            available: true,
            actor_type: this._actorType(actor),
            parent: this._actorLabel(parent),
            parent_index: this._actorIndexInParent(parent, actor),
            visible: this._actorBoolean(actor, 'visible'),
            mapped: this._actorBoolean(actor, 'mapped'),
            reactive: this._actorBoolean(actor, 'reactive'),
            bounds: this._shellActorBounds(actor),
            child_count: children.length,
            children: this._actorChildSummaries(actor, options),
            children_truncated: children.length > SHELL_ACTOR_GROUP_DIAGNOSTIC_CHILD_LIMIT,
        };
    }

    _shellActorChildOrder(name, options = {}) {
        const actor = this._globalActorByName(name);
        return this._actorChildOrder(name, actor, options);
    }

    _actorChildOrder(parentLabel, actor, options = {}) {
        const children = this._actorChildren(actor);
        return {
            parent: parentLabel,
            available: Boolean(actor),
            child_count: children.length,
            children: this._actorChildSummaries(actor, options),
            children_truncated: children.length > SHELL_ACTOR_GROUP_DIAGNOSTIC_CHILD_LIMIT,
        };
    }

    _uiGroupActor() {
        const windowGroupParent = this._actorParent(this._globalActorByName('global.window_group'));
        if (windowGroupParent) {
            return windowGroupParent;
        }
        return this._actorChildren(this._globalActorByName('global.stage'))
            .find(actor => this._actorName(actor) === 'uiGroup' || this._actorType(actor) === 'UiActor') || null;
    }

    _globalActorByName(name) {
        if (!name?.startsWith?.('global.')) {
            return null;
        }
        const key = name.slice('global.'.length);
        try {
            return global?.[key] || null;
        } catch (_error) {
            return null;
        }
    }

    _actorChildren(actor) {
        try {
            return actor?.get_children?.() || [];
        } catch (_error) {
            return [];
        }
    }

    _actorParent(actor) {
        try {
            return actor?.get_parent?.() || null;
        } catch (_error) {
            return null;
        }
    }

    _actorChildSummaries(actor, options = {}) {
        return this._actorChildren(actor)
            .slice(0, SHELL_ACTOR_GROUP_DIAGNOSTIC_CHILD_LIMIT)
            .map((child, index) => this._actorSummary(child, index, options));
    }

    _actorSummary(actor, index = null, options = {}) {
        const summary = {
            index,
            label: this._actorLabel(actor),
            actor_type: this._actorType(actor),
            name: this._actorName(actor),
            visible: this._actorBoolean(actor, 'visible'),
            mapped: this._actorBoolean(actor, 'mapped'),
            reactive: this._actorBoolean(actor, 'reactive'),
            bounds: this._shellActorBounds(actor),
            child_count: this._actorChildren(actor).length,
        };
        if (options.includeWindowDetails) {
            summary.window = this._windowActorPayload(actor, options.targetToken || '');
        }
        return summary;
    }

    _windowActorPayload(actor, targetToken = '') {
        const window = this._metaWindowForActor(actor);
        if (!window) {
            return null;
        }
        const tracker = Shell.WindowTracker.get_default();
        const payload = this._windowPayload(window, tracker);
        return {
            target_token: payload.targetToken,
            target_token_match: Boolean(targetToken && payload.targetToken === targetToken),
            title: payload.title,
            wm_class: payload.wmClass,
            wm_class_instance: payload.wmClassInstance,
            app_id: payload.appId,
            app_name: payload.appName,
            pid: payload.pid,
            monitor: payload.monitor,
            fullscreen: payload.fullscreen,
            has_focus: payload.hasFocus,
            showing_on_workspace: payload.showingOnWorkspace,
            minimized: payload.minimized,
            workspace: payload.workspace,
            frame_rect: payload.frameRect,
            buffer_rect: payload.bufferRect,
            content_rect: payload.contentRect,
        };
    }

    _targetWindowActorDiagnostic(targetToken = '') {
        if (!targetToken) {
            return null;
        }
        const windowGroup = this._globalActorByName('global.window_group');
        const matches = this._actorChildren(windowGroup)
            .map((child, index) => this._actorSummary(
                child,
                index,
                { targetToken, includeWindowDetails: true },
            ))
            .filter(summary => Boolean(summary.window?.target_token_match));
        return {
            target_token: targetToken,
            window_group_available: Boolean(windowGroup),
            match_count: matches.length,
            matches,
        };
    }

    _shellActorProofDiagnostic() {
        const actor = this._shellActorProof?.actor || null;
        const parent = this._actorParent(actor);
        const parentIndex = this._actorIndexInParent(parent, actor);
        return {
            actor_visible: Boolean(actor),
            actor_parent: this._shellActorProof?.actorParent || '',
            parent: this._actorLabel(parent),
            parent_index: parentIndex,
            sibling_index: parentIndex,
            visible: this._actorBoolean(actor, 'visible'),
            mapped: this._actorBoolean(actor, 'mapped'),
            reactive: this._actorBoolean(actor, 'reactive'),
            bounds: this._shellActorBounds(actor),
            child_count: this._actorChildren(actor).length,
        };
    }

    _metaWindowForActor(actor) {
        try {
            return actor?.get_meta_window?.() || null;
        } catch (_error) {
            return null;
        }
    }

    _actorIndexInParent(parent, actor) {
        if (!parent || !actor) {
            return null;
        }
        const children = this._actorChildren(parent);
        const index = children.indexOf(actor);
        return index >= 0 ? index : null;
    }

    _actorLabel(actor) {
        const type = this._actorType(actor);
        const name = this._actorName(actor);
        if (type && name) {
            return `${type}:${name}`;
        }
        return type || name || '';
    }

    _actorType(actor) {
        if (!actor) {
            return '';
        }
        try {
            return String(actor.constructor?.name || actor.toString?.() || '');
        } catch (_error) {
            return '';
        }
    }

    _actorName(actor) {
        if (!actor) {
            return '';
        }
        try {
            return String(actor.get_name?.() || actor.name || '');
        } catch (_error) {
            return '';
        }
    }

    _actorBoolean(actor, key) {
        if (!actor || actor[key] === undefined || actor[key] === null) {
            return null;
        }
        return Boolean(actor[key]);
    }

    _shellActorBounds(actor) {
        if (!actor) {
            return null;
        }
        return {
            x: Math.round(Number(actor.x) || 0),
            y: Math.round(Number(actor.y) || 0),
            width: Math.round(Number(actor.width) || 0),
            height: Math.round(Number(actor.height) || 0),
        };
    }

    _shellActorProofPayload({
        requestedAction,
        visible,
        requestedRect = null,
        targetToken = '',
        targetPayload = null,
        appliedRect = null,
        actorParent = '',
        eligible = true,
        eligibilityReasons = [],
        cleanupAction = '',
        staleTimeoutSeconds = SHELL_ACTOR_PROOF_TIMEOUT_MS / 1000,
        groupDiagnostics = null,
    }) {
        const payload = {
            schema: 1,
            requested: Boolean(requestedAction),
            action: requestedAction,
            actor_visible: Boolean(visible),
            requested_rect: requestedRect,
            applied_actor_bounds: appliedRect,
            target_token: targetToken,
            target_monitor: targetPayload?.monitor ?? null,
            target_monitor_rect: targetPayload?.monitorRect || null,
            actor_parent: actorParent || this._shellActorProof?.actorParent || '',
            eligible,
            eligibility_reasons: eligibilityReasons,
            stale_timeout_seconds: staleTimeoutSeconds,
            cleanup_action: cleanupAction,
        };
        if (groupDiagnostics) {
            payload.group_diagnostics = groupDiagnostics;
        }
        return payload;
    }

    _refreshShellActorProofTimeout() {
        if (this._shellActorProofTimeoutId) {
            GLib.source_remove(this._shellActorProofTimeoutId);
            this._shellActorProofTimeoutId = 0;
        }
        this._shellActorProofTimeoutId = GLib.timeout_add(
            GLib.PRIORITY_DEFAULT,
            SHELL_ACTOR_PROOF_TIMEOUT_MS,
            () => {
                this._clearShellActorProof('stale_timeout');
                return GLib.SOURCE_REMOVE;
            },
        );
    }

    _clearShellActorProof(reason = 'clear') {
        const hadActor = Boolean(this._shellActorProof?.actor);
        const proof = this._shellActorProof;
        if (this._shellActorProofTimeoutId) {
            GLib.source_remove(this._shellActorProofTimeoutId);
            this._shellActorProofTimeoutId = 0;
        }
        this._shellActorProof = null;
        try {
            const parent = proof?.actor?.get_parent?.();
            if (parent && typeof parent.remove_child === 'function') {
                parent.remove_child(proof.actor);
            }
        } catch (_error) {
            // Best-effort cleanup only; diagnostics report the requested cleanup reason.
        }
        try {
            proof?.actor?.destroy?.();
        } catch (_error) {
            // Best-effort cleanup only; diagnostics report the requested cleanup reason.
        }
        return hadActor ? reason : '';
    }

    _findOverlayWindow(entries, request, targetToken) {
        const overlayTitle = this._requestString(request, 'overlay_title', 'overlayTitle') || 'EDMC Modern Overlay';
        const overlayWmClass = this._requestString(request, 'overlay_wm_class', 'overlayWmClass') || 'EDMCModernOverlay';
        const lowerTitle = overlayTitle.toLowerCase();
        const lowerClass = overlayWmClass.toLowerCase();
        return entries.find(entry => {
            const payload = entry.payload;
            if (!payload || payload.targetToken === targetToken) {
                return false;
            }
            const title = String(payload.title || '').toLowerCase();
            const wmClass = String(payload.wmClass || '').toLowerCase();
            const wmClassInstance = String(payload.wmClassInstance || '').toLowerCase();
            const appName = String(payload.appName || '').toLowerCase();
            const appId = String(payload.appId || '').toLowerCase();
            return title === lowerTitle ||
                wmClass === lowerClass ||
                wmClassInstance === lowerClass ||
                appName === lowerTitle ||
                appId === lowerClass;
        }) || null;
    }

    _applyOverlayPresentation(window, requestedRect, rectTolerance = 2, options = {}) {
        const unsupportedFeatures = [];
        const degradeReasons = [];
        let placement = false;
        let stacking = false;
        let appliedRect = null;
        let moveResizeAction = 'not_attempted';
        let strategyProbeDiagnostics = null;
        const strategyProbe = this._normalisePresentationStrategyProbe(
            options.presentationStrategyProbe,
            options.includePresentationStrategyDiagnostics,
        );
        const currentFrameRect = this._rectPayload(this._safeCall(window, 'get_frame_rect'));
        const preBufferRect = this._rectPayload(this._safeCall(window, 'get_buffer_rect'));
        const preMonitor = this._safeCall(window, 'get_monitor');
        if (strategyProbe) {
            strategyProbeDiagnostics = this._applyPresentationStrategyProbe(
                window,
                strategyProbe,
                requestedRect,
                rectTolerance,
                options.targetPayload,
            );
            placement = Boolean(strategyProbeDiagnostics.placement);
            appliedRect = strategyProbeDiagnostics.appliedRect || null;
            moveResizeAction = `strategy_probe:${strategyProbeDiagnostics.strategy || strategyProbe}`;
            if (!strategyProbeDiagnostics.eligible) {
                degradeReasons.push('presentation_strategy_probe_ineligible');
            }
            if (strategyProbeDiagnostics.error) {
                degradeReasons.push('presentation_strategy_probe_error');
            }
            if (!placement) {
                degradeReasons.push('placement_unproven');
            }
        } else {
            try {
                if (
                    currentFrameRect &&
                    this._rectIsValid(currentFrameRect) &&
                    this._rectsMatchWithinTolerance(currentFrameRect, requestedRect, rectTolerance)
                ) {
                    placement = true;
                    appliedRect = currentFrameRect;
                    moveResizeAction = 'skipped_matching_frame';
                } else if (typeof window?.move_resize_frame === 'function') {
                    window.move_resize_frame(
                        false,
                        requestedRect.x,
                        requestedRect.y,
                        requestedRect.width,
                        requestedRect.height,
                    );
                    placement = true;
                    moveResizeAction = 'move_resize_frame';
                } else if (typeof window?.move_frame === 'function') {
                    window.move_frame(false, requestedRect.x, requestedRect.y);
                    unsupportedFeatures.push('resize_frame');
                    degradeReasons.push('placement_size_unproven');
                    moveResizeAction = 'move_frame';
                } else {
                    unsupportedFeatures.push('move_resize_frame');
                    degradeReasons.push('placement_unproven');
                    moveResizeAction = 'unsupported';
                }
            } catch (_error) {
                placement = false;
                degradeReasons.push('placement_error');
                moveResizeAction = 'error';
            }
        }
        try {
            if (typeof window?.make_above === 'function') {
                window.make_above();
                stacking = true;
            } else {
                unsupportedFeatures.push('make_above');
                degradeReasons.push('stacking_unproven');
            }
        } catch (_error) {
            stacking = false;
            degradeReasons.push('stacking_error');
        }
        const frameRect = this._rectPayload(this._safeCall(window, 'get_frame_rect'));
        const postBufferRect = this._rectPayload(this._safeCall(window, 'get_buffer_rect'));
        const postMonitor = this._safeCall(window, 'get_monitor');
        if (frameRect && this._rectIsValid(frameRect)) {
            appliedRect = strategyProbeDiagnostics?.appliedRect || frameRect;
        } else if (placement) {
            appliedRect = appliedRect || requestedRect;
        }
        if (
            placement &&
            appliedRect &&
            requestedRect &&
            this._rectIsValid(appliedRect) &&
            this._rectIsValid(requestedRect) &&
            !this._rectsMatchWithinTolerance(appliedRect, requestedRect, rectTolerance)
        ) {
            degradeReasons.push('applied_rect_mismatch');
        }
        const presentationDiagnostics = (options.includePresentationDiagnostics || strategyProbeDiagnostics)
            ? this._presentationDiagnosticsPayload({
                requestedRect,
                overlayPayload: options.overlayPayload,
                targetPayload: options.targetPayload,
                moveResizeAction,
                preFrameRect: currentFrameRect,
                preBufferRect,
                preMonitor,
                postFrameRect: frameRect,
                postBufferRect,
                postMonitor,
                strategyProbeDiagnostics,
            })
            : null;
        return {
            placement,
            stacking,
            appliedRect,
            unsupportedFeatures,
            degradeReasons,
            presentationDiagnostics,
        };
    }

    _presentationDiagnosticsPayload({
        requestedRect,
        overlayPayload,
        targetPayload,
        moveResizeAction,
        preFrameRect,
        preBufferRect,
        preMonitor,
        postFrameRect,
        postBufferRect,
        postMonitor,
        strategyProbeDiagnostics,
    }) {
        const payload = {
            schema: 1,
            requestedRect,
            target: {
                targetToken: targetPayload?.targetToken || '',
                monitor: targetPayload?.monitor ?? null,
                monitorRect: targetPayload?.monitorRect || null,
                frameRect: targetPayload?.frameRect || null,
                bufferRect: targetPayload?.bufferRect || null,
                contentRect: targetPayload?.contentRect || null,
                fullscreen: Boolean(targetPayload?.fullscreen),
                showingOnWorkspace: Boolean(targetPayload?.showingOnWorkspace),
            },
            overlay: {
                targetToken: overlayPayload?.targetToken || '',
                title: overlayPayload?.title || '',
                wmClass: overlayPayload?.wmClass || '',
                wmClassInstance: overlayPayload?.wmClassInstance || '',
                appId: overlayPayload?.appId || '',
                appName: overlayPayload?.appName || '',
            },
            placement: {
                moveResizeAction,
            },
            before: {
                frameRect: preFrameRect,
                bufferRect: preBufferRect,
                monitor: preMonitor ?? null,
            },
            after: {
                frameRect: postFrameRect,
                bufferRect: postBufferRect,
                monitor: postMonitor ?? null,
            },
        };
        if (strategyProbeDiagnostics) {
            payload.strategyProbe = strategyProbeDiagnostics;
        }
        return payload;
    }

    _normalisePresentationStrategyProbe(rawStrategy, includePresentationStrategyDiagnostics) {
        const strategy = String(rawStrategy || '').trim();
        if (strategy) {
            return strategy;
        }
        return includePresentationStrategyDiagnostics ? 'normal_move_resize' : '';
    }

    _applyPresentationStrategyProbe(window, strategy, requestedRect, rectTolerance, targetPayload) {
        const normalisedStrategy = PRESENTATION_STRATEGY_PROBES.includes(strategy)
            ? strategy
            : '';
        const before = this._presentationProbeWindowState(window);
        const methodAvailability = this._presentationProbeMethodAvailability(window);
        const eligibility = this._presentationStrategyEligibility(targetPayload, requestedRect, rectTolerance);
        const diagnostics = {
            schema: 1,
            requestedStrategy: strategy,
            strategy: normalisedStrategy || strategy,
            knownStrategies: PRESENTATION_STRATEGY_PROBES,
            eligible: eligibility.eligible && Boolean(normalisedStrategy),
            eligibilityReasons: normalisedStrategy ? eligibility.reasons : ['unsupported_strategy'],
            methodAvailability,
            requestedRect,
            target: {
                targetToken: targetPayload?.targetToken || '',
                monitor: targetPayload?.monitor ?? null,
                monitorRect: targetPayload?.monitorRect || null,
                contentRect: targetPayload?.contentRect || null,
                fullscreen: Boolean(targetPayload?.fullscreen),
            },
            before,
            actions: [],
            after: null,
            appliedRect: null,
            rectMatch: false,
            monitorChanged: false,
            fullscreenChanged: false,
            placement: false,
            error: '',
            restoration: {
                attempted: false,
                actions: [],
                after: null,
                restoredFrame: null,
                detail: '',
            },
        };
        if (!diagnostics.eligible) {
            diagnostics.after = this._presentationProbeWindowState(window);
            diagnostics.appliedRect = diagnostics.after.frameRect;
            diagnostics.rectMatch = this._rectsMatchWithinTolerance(
                diagnostics.appliedRect,
                requestedRect,
                rectTolerance,
            );
            return diagnostics;
        }

        try {
            this._runPresentationStrategyProbe(window, normalisedStrategy, requestedRect, targetPayload, diagnostics);
        } catch (error) {
            diagnostics.error = this._errorMessage(error);
        }
        const strategyAfter = this._presentationProbeWindowState(window);
        diagnostics.after = strategyAfter;
        diagnostics.appliedRect = strategyAfter.frameRect;
        diagnostics.rectMatch = this._rectsMatchWithinTolerance(strategyAfter.frameRect, requestedRect, rectTolerance);
        diagnostics.monitorChanged = before.monitor !== strategyAfter.monitor;
        diagnostics.fullscreenChanged = before.fullscreen !== strategyAfter.fullscreen;
        diagnostics.placement = diagnostics.actions.some(action => action.ok);

        if (this._strategyUsesFullscreen(normalisedStrategy) && !before.fullscreen) {
            this._restoreAfterFullscreenProbe(window, before, diagnostics.restoration);
        }
        return diagnostics;
    }

    _presentationStrategyEligibility(targetPayload, requestedRect, rectTolerance) {
        const reasons = [];
        const contentRect = targetPayload?.contentRect || null;
        const monitorRect = targetPayload?.monitorRect || null;
        if (!targetPayload?.fullscreen) {
            reasons.push('target_not_fullscreen');
        }
        if (!this._rectIsValid(contentRect)) {
            reasons.push('missing_target_content_rect');
        }
        if (!this._rectIsValid(monitorRect)) {
            reasons.push('missing_target_monitor_rect');
        }
        if (!this._rectIsValid(requestedRect)) {
            reasons.push('invalid_requested_rect');
        }
        if (
            this._rectIsValid(contentRect) &&
            this._rectIsValid(monitorRect) &&
            !this._rectsMatchWithinTolerance(contentRect, monitorRect, rectTolerance)
        ) {
            reasons.push('target_content_rect_not_monitor_bounds');
        }
        if (
            this._rectIsValid(requestedRect) &&
            this._rectIsValid(monitorRect) &&
            !this._rectsMatchWithinTolerance(requestedRect, monitorRect, rectTolerance)
        ) {
            reasons.push('requested_rect_not_monitor_bounds');
        }
        return {
            eligible: reasons.length === 0,
            reasons,
        };
    }

    _runPresentationStrategyProbe(window, strategy, requestedRect, targetPayload, diagnostics) {
        switch (strategy) {
        case 'normal_move_resize':
            this._probeMoveResize(window, requestedRect, diagnostics.actions);
            break;
        case 'move_to_monitor_then_resize':
            this._probeMoveToMonitor(window, targetPayload?.monitor, diagnostics.actions);
            this._probeMoveResize(window, requestedRect, diagnostics.actions);
            break;
        case 'resize_then_move_to_monitor':
            this._probeMoveResize(window, requestedRect, diagnostics.actions);
            this._probeMoveToMonitor(window, targetPayload?.monitor, diagnostics.actions);
            break;
        case 'make_fullscreen_then_resize':
            this._probeMakeFullscreen(window, diagnostics.actions);
            this._probeMoveResize(window, requestedRect, diagnostics.actions);
            break;
        case 'resize_then_make_fullscreen':
            this._probeMoveResize(window, requestedRect, diagnostics.actions);
            this._probeMakeFullscreen(window, diagnostics.actions);
            break;
        case 'fullscreen_only':
            this._probeMakeFullscreen(window, diagnostics.actions);
            break;
        default:
            diagnostics.error = 'unsupported strategy';
            break;
        }
    }

    _probeMoveResize(window, requestedRect, actions) {
        const currentFrameRect = this._rectPayload(this._safeCall(window, 'get_frame_rect'));
        if (
            currentFrameRect &&
            this._rectIsValid(currentFrameRect) &&
            this._rectsMatchWithinTolerance(currentFrameRect, requestedRect, 0)
        ) {
            actions.push({
                name: 'skip_matching_frame',
                method: 'get_frame_rect',
                available: true,
                ok: true,
                error: '',
            });
            return;
        }
        if (typeof window?.move_resize_frame === 'function') {
            this._recordPresentationProbeAction(actions, 'move_resize_frame', () => {
                window.move_resize_frame(
                    false,
                    requestedRect.x,
                    requestedRect.y,
                    requestedRect.width,
                    requestedRect.height,
                );
            });
            return;
        }
        if (typeof window?.move_frame === 'function') {
            this._recordPresentationProbeAction(actions, 'move_frame', () => {
                window.move_frame(false, requestedRect.x, requestedRect.y);
            });
            return;
        }
        actions.push({
            name: 'move_resize_frame',
            method: 'move_resize_frame',
            available: false,
            ok: false,
            error: 'method unavailable',
        });
    }

    _probeMoveToMonitor(window, monitorIndex, actions) {
        if (typeof window?.move_to_monitor !== 'function') {
            actions.push({
                name: 'move_to_monitor',
                method: 'move_to_monitor',
                available: false,
                ok: false,
                error: 'method unavailable',
            });
            return;
        }
        const index = this._normaliseMonitorIndex(monitorIndex);
        if (index === null) {
            actions.push({
                name: 'move_to_monitor',
                method: 'move_to_monitor',
                available: true,
                ok: false,
                error: 'target monitor unavailable',
            });
            return;
        }
        this._recordPresentationProbeAction(actions, 'move_to_monitor', () => {
            window.move_to_monitor(index);
        });
    }

    _probeMakeFullscreen(window, actions) {
        if (typeof window?.make_fullscreen !== 'function') {
            actions.push({
                name: 'make_fullscreen',
                method: 'make_fullscreen',
                available: false,
                ok: false,
                error: 'method unavailable',
            });
            return;
        }
        this._recordPresentationProbeAction(actions, 'make_fullscreen', () => {
            window.make_fullscreen();
        });
    }

    _restoreAfterFullscreenProbe(window, before, restoration) {
        restoration.attempted = true;
        if (typeof window?.unmake_fullscreen === 'function') {
            this._recordPresentationProbeAction(restoration.actions, 'unmake_fullscreen', () => {
                window.unmake_fullscreen();
            });
        } else {
            restoration.actions.push({
                name: 'unmake_fullscreen',
                method: 'unmake_fullscreen',
                available: false,
                ok: false,
                error: 'method unavailable',
            });
        }
        if (this._rectIsValid(before.frameRect) && typeof window?.move_resize_frame === 'function') {
            this._recordPresentationProbeAction(restoration.actions, 'restore_move_resize_frame', () => {
                window.move_resize_frame(
                    false,
                    before.frameRect.x,
                    before.frameRect.y,
                    before.frameRect.width,
                    before.frameRect.height,
                );
            });
        } else {
            restoration.actions.push({
                name: 'restore_move_resize_frame',
                method: 'move_resize_frame',
                available: typeof window?.move_resize_frame === 'function',
                ok: false,
                error: 'pre-probe frame unavailable or method unavailable',
            });
        }
        restoration.after = this._presentationProbeWindowState(window);
        restoration.restoredFrame = this._rectsMatchWithinTolerance(
            restoration.after.frameRect,
            before.frameRect,
            2,
        );
    }

    _recordPresentationProbeAction(actions, method, callback) {
        try {
            callback();
            actions.push({
                name: method,
                method,
                available: true,
                ok: true,
                error: '',
            });
        } catch (error) {
            actions.push({
                name: method,
                method,
                available: true,
                ok: false,
                error: this._errorMessage(error),
            });
        }
    }

    _presentationProbeWindowState(window) {
        return {
            frameRect: this._rectPayload(this._safeCall(window, 'get_frame_rect')),
            bufferRect: this._rectPayload(this._safeCall(window, 'get_buffer_rect')),
            monitor: this._safeCall(window, 'get_monitor'),
            fullscreen: Boolean(window?.fullscreen || window?.is_fullscreen?.()),
            workspace: this._workspaceName(window),
        };
    }

    _presentationProbeMethodAvailability(window) {
        return {
            move_to_monitor: typeof window?.move_to_monitor === 'function',
            move_resize_frame: typeof window?.move_resize_frame === 'function',
            move_frame: typeof window?.move_frame === 'function',
            make_fullscreen: typeof window?.make_fullscreen === 'function',
            unmake_fullscreen: typeof window?.unmake_fullscreen === 'function',
            make_above: typeof window?.make_above === 'function',
            change_workspace: typeof window?.change_workspace === 'function',
            move_to_workspace: typeof window?.move_to_workspace === 'function',
            stick: typeof window?.stick === 'function',
        };
    }

    _strategyUsesFullscreen(strategy) {
        return strategy === 'make_fullscreen_then_resize' ||
            strategy === 'resize_then_make_fullscreen' ||
            strategy === 'fullscreen_only';
    }

    _errorMessage(error) {
        return String(error?.message || error || '');
    }

    _windowChromeFree(payload) {
        const insets = payload?.decorationInsets;
        if (!insets) {
            return false;
        }
        return Number(insets.left || 0) === 0 &&
            Number(insets.top || 0) === 0 &&
            Number(insets.right || 0) === 0 &&
            Number(insets.bottom || 0) === 0;
    }

    _parseJsonObject(rawValue) {
        try {
            const parsed = JSON.parse(this._jsonStringPayload(rawValue));
            if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
                return { ok: false, detail: 'request must be a JSON object' };
            }
            return { ok: true, value: parsed };
        } catch (_error) {
            return { ok: false, detail: 'request is not valid JSON' };
        }
    }

    _jsonStringPayload(rawValue) {
        let value = this._deepUnpack(rawValue);
        if (Array.isArray(value) && value.length === 1) {
            value = this._deepUnpack(value[0]);
        }
        return String(value || '{}');
    }

    _requestString(payload, ...names) {
        for (const name of names) {
            const value = payload?.[name];
            if (value !== null && value !== undefined) {
                return String(value).trim();
            }
        }
        return '';
    }

    _requestBool(payload, ...names) {
        for (const name of names) {
            const value = payload?.[name];
            if (value === null || value === undefined) {
                continue;
            }
            if (typeof value === 'string') {
                return ['1', 'true', 'yes', 'on'].includes(value.trim().toLowerCase());
            }
            return Boolean(value);
        }
        return false;
    }

    _requestInt(payload, fallback, ...names) {
        for (const name of names) {
            const value = payload?.[name];
            if (value === null || value === undefined) {
                continue;
            }
            const parsed = Number.parseInt(String(value), 10);
            if (Number.isFinite(parsed)) {
                return parsed;
            }
        }
        return fallback;
    }

    _requestStringList(payload, ...names) {
        for (const name of names) {
            const value = payload?.[name];
            if (Array.isArray(value)) {
                return value.map(item => String(item).trim()).filter(item => item);
            }
            if (typeof value === 'string' && value.trim()) {
                return [value.trim()];
            }
        }
        return [];
    }

    _requestObject(payload, ...names) {
        for (const name of names) {
            const value = payload?.[name];
            if (value && typeof value === 'object' && !Array.isArray(value)) {
                return value;
            }
        }
        return null;
    }

    _requestArray(payload, ...names) {
        for (const name of names) {
            const value = payload?.[name];
            if (Array.isArray(value)) {
                return value;
            }
        }
        return [];
    }

    _requestRect(payload, ...names) {
        for (const name of names) {
            const rect = this._rectPayload(payload?.[name]);
            if (rect && this._rectIsValid(rect)) {
                return rect;
            }
        }
        return null;
    }
}

export default class EdmcModernOverlayHelperExtension extends Extension {
    enable() {
        this._helperIdentity = {
            uuid: HELPER_UUID,
            helperKind: HELPER_KIND,
            helperProtocol: HELPER_PROTOCOL,
            helperVersion: HELPER_VERSION,
        };
        this._healthService = new HelperHealthService();
        this._dbusObject = Gio.DBusExportedObject.wrapJSObject(
            HELPER_DBUS_XML,
            this._healthService,
        );
        this._dbusExported = false;
        this._busOwnerId = Gio.bus_own_name(
            Gio.BusType.SESSION,
            HELPER_DBUS_SERVICE,
            Gio.BusNameOwnerFlags.REPLACE,
            connection => {
                if (this._dbusObject) {
                    this._dbusObject.export(connection, HELPER_DBUS_OBJECT_PATH);
                    this._dbusExported = true;
                }
            },
            null,
            () => {
                this._unexportDbusObject();
            },
        );
    }

    disable() {
        if (this._busOwnerId) {
            Gio.bus_unown_name(this._busOwnerId);
            this._busOwnerId = 0;
        }
        this._healthService?._clearShellActorProof?.('helper_disable');
        this._healthService?._clearShellRasterFrame?.('helper_disable');
        this._healthService?._disconnectShellRasterOverviewSignals?.();
        this._unexportDbusObject();
        this._healthService = null;
        this._helperIdentity = null;
    }

    _unexportDbusObject() {
        if (!this._dbusObject) {
            return;
        }
        if (this._dbusExported) {
            this._dbusObject.unexport();
        }
        this._dbusObject = null;
        this._dbusExported = false;
    }
}
