import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Shell from 'gi://Shell';
import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';

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

class HelperHealthService {
    constructor() {
        this._startedAtUnixMs = Date.now();
        this._startedAtMonotonicUs = GLib.get_monotonic_time();
        this._targetSequence = 0;
        this._presentationSequence = 0;
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
        const windows = this._enumerateWindows();
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
        const standaloneMode = this._requestBool(payload, 'standalone_mode', 'standaloneMode');
        const base = {
            action,
            targetToken,
            requestedRect,
            standaloneMode,
            generatedAtUnixMs,
            generatedAtMonotonicUs,
        };

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

        const result = this._applyOverlayPresentation(overlayEntry.window, requestedRect);
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
            detail: status === 'presentation_applied' ? '' : 'required presentation gate unproven',
        }));
    }

    _enumerateWindows() {
        return this._enumerateWindowEntries().map(entry => entry.payload);
    }

    _enumerateWindowEntries() {
        const tracker = Shell.WindowTracker.get_default();
        return global.get_window_actors()
            .map(actor => actor?.get_meta_window?.())
            .filter(window => window)
            .map(window => ({
                window,
                payload: this._windowPayload(window, tracker),
            }));
    }

    _windowPayload(window, tracker) {
        const app = tracker?.get_window_app?.(window);
        const frameRect = this._rectPayload(this._safeCall(window, 'get_frame_rect'));
        const bufferRect = this._rectPayload(this._safeCall(window, 'get_buffer_rect'));
        const contentRect = this._contentRectPayload(window, frameRect, bufferRect);
        return {
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
            monitor: this._safeCall(window, 'get_monitor'),
            outputName: this._outputName(this._safeCall(window, 'get_monitor')),
            monitorScale: this._monitorScale(this._safeCall(window, 'get_monitor')),
            hasFocus: Boolean(window?.has_focus?.()),
            showingOnWorkspace: Boolean(window?.showing_on_its_workspace?.()),
            minimized: Boolean(window?.minimized),
            fullscreen: Boolean(window?.fullscreen || window?.is_fullscreen?.()),
            workspace: this._workspaceName(window),
        };
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
        return {
            left: contentRect.x - frameRect.x,
            top: contentRect.y - frameRect.y,
            right: (frameRect.x + frameRect.width) - (contentRect.x + contentRect.width),
            bottom: (frameRect.y + frameRect.height) - (contentRect.y + contentRect.height),
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

    _outputName(monitorIndex) {
        const monitor = this._monitorForIndex(monitorIndex);
        return String(monitor?.connector || monitor?.get_connector?.() || '');
    }

    _monitorScale(monitorIndex) {
        const monitor = this._monitorForIndex(monitorIndex);
        const scale = monitor?.scale_factor || monitor?.get_scale_factor?.();
        return scale === undefined ? null : scale;
    }

    _monitorForIndex(monitorIndex) {
        try {
            if (monitorIndex === null || monitorIndex === undefined || !global.display?.get_monitor_geometry) {
                return null;
            }
            return global.display.get_monitor_geometry(monitorIndex);
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
        detail = '',
    }) {
        return {
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

    _applyOverlayPresentation(window, requestedRect) {
        const unsupportedFeatures = [];
        const degradeReasons = [];
        let placement = false;
        let stacking = false;
        let appliedRect = null;
        try {
            if (typeof window?.move_resize_frame === 'function') {
                window.move_resize_frame(
                    false,
                    requestedRect.x,
                    requestedRect.y,
                    requestedRect.width,
                    requestedRect.height,
                );
                placement = true;
            } else if (typeof window?.move_frame === 'function') {
                window.move_frame(false, requestedRect.x, requestedRect.y);
                unsupportedFeatures.push('resize_frame');
                degradeReasons.push('placement_size_unproven');
            } else {
                unsupportedFeatures.push('move_resize_frame');
                degradeReasons.push('placement_unproven');
            }
        } catch (_error) {
            placement = false;
            degradeReasons.push('placement_error');
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
        if (frameRect && this._rectIsValid(frameRect)) {
            appliedRect = frameRect;
        } else if (placement) {
            appliedRect = requestedRect;
        }
        return { placement, stacking, appliedRect, unsupportedFeatures, degradeReasons };
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
            const parsed = JSON.parse(String(rawValue || '{}'));
            if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
                return { ok: false, detail: 'request must be a JSON object' };
            }
            return { ok: true, value: parsed };
        } catch (_error) {
            return { ok: false, detail: 'request is not valid JSON' };
        }
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
