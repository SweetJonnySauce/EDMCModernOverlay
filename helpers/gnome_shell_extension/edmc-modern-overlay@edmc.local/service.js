import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

export const HELPER_KIND = 'gnome_shell_extension';
export const HELPER_PROTOCOL_VERSION = 1;
export const HELPER_VERSION = 'stage5.4.2';
export const HELPER_SERVICE_NAME = 'org.edmc.EDMCModernOverlay';
export const HELPER_OBJECT_PATH = '/org/edmc/EDMCModernOverlay';
export const HELPER_INTERFACE_NAME = 'org.edmc.EDMCModernOverlay.Helper';

const TITLE_PATTERN = /elite\s*-\s*dangerous/i;
const OVERLAY_TITLE_PATTERN = /^edmc modern overlay$/i;
const FOREGROUND_LOSS_HOLD_MS = 900;
const SHELL_CHROME_REAPPLY_MS = 250;

const INTERFACE_XML = `
<node>
  <interface name="org.edmc.EDMCModernOverlay.Helper">
    <method name="Hello">
      <arg name="session_token" type="s" direction="in"/>
      <arg name="helper_kind" type="s" direction="out"/>
      <arg name="protocol_version" type="u" direction="out"/>
      <arg name="helper_version" type="s" direction="out"/>
    </method>
    <method name="SetOverlayInputPassthrough">
      <arg name="enabled" type="b" direction="in"/>
      <arg name="applied" type="b" direction="out"/>
    </method>
    <property name="HelperKind" type="s" access="read"/>
    <property name="ProtocolVersion" type="u" access="read"/>
    <property name="HelperVersion" type="s" access="read"/>
    <property name="SessionReady" type="b" access="read"/>
    <signal name="Event">
      <arg name="message_json" type="s"/>
    </signal>
  </interface>
</node>`;

export class EDMCModernOverlayHelperService {
    constructor({uuid = ''} = {}) {
        this._uuid = String(uuid || '').trim();
        this._ownerId = 0;
        this._impl = null;
        this._sessionToken = '';
        this._display = null;
        this._displaySignalIds = [];
        this._trackedWindow = null;
        this._trackedWindowSignalIds = [];
        this._overlayWindow = null;
        this._overlayWindowSignalIds = [];
        this._lastActiveEventJson = '';
        this._lastGeometryEventJson = '';
        this._lastPresentationEventJson = '';
        this._lastForegroundWindowId = '';
        this._lastForegroundTimestampMs = 0;
        this._overlayInputPassthroughRequested = true;
        this._panelChromeState = [];
        this._dockChromeState = [];
        this._shellChromeHidden = false;
        this._shellChromeMaintenanceSourceId = 0;
    }

    get HelperKind() {
        return HELPER_KIND;
    }

    get ProtocolVersion() {
        return HELPER_PROTOCOL_VERSION;
    }

    get HelperVersion() {
        return HELPER_VERSION;
    }

    get SessionReady() {
        return this._sessionToken.length > 0;
    }

    enable() {
        if (this._ownerId !== 0)
            return;

        this._connectDisplaySignals();
        this._ownerId = Gio.bus_own_name(
            Gio.BusType.SESSION,
            HELPER_SERVICE_NAME,
            Gio.BusNameOwnerFlags.NONE,
            this._onBusAcquired.bind(this),
            this._onNameAcquired.bind(this),
            this._onNameLost.bind(this));
    }

    disable() {
        this._disconnectTrackedWindowSignals();
        this._disconnectOverlayWindowSignals();
        this._disconnectDisplaySignals();
        if (this._impl !== null) {
            this._impl.unexport();
            this._impl = null;
        }

        if (this._ownerId !== 0) {
            Gio.bus_unown_name(this._ownerId);
            this._ownerId = 0;
        }

        this._sessionToken = '';
        this._lastActiveEventJson = '';
        this._lastGeometryEventJson = '';
        this._lastPresentationEventJson = '';
        this._clearForegroundHold();
        this._stopShellChromeMaintenance();
        this._restoreShellChrome();
    }

    Hello(sessionToken) {
        const token = String(sessionToken ?? '').trim();
        if (!token)
            throw new Error('session_token is required');

        const sessionChanged = token !== this._sessionToken;
        this._sessionToken = token;
        if (sessionChanged) {
            this._lastActiveEventJson = '';
            this._lastGeometryEventJson = '';
            this._lastPresentationEventJson = '';
        }
        this._emitPropertyChanged('SessionReady', GLib.Variant.new_boolean(this.SessionReady));
        this._refreshTrackedWindow({emitActive: true, emitGeometry: true, emitPresentation: true, force: true});
        return [HELPER_KIND, HELPER_PROTOCOL_VERSION, HELPER_VERSION];
    }

    SetOverlayInputPassthrough(enabled) {
        this._overlayInputPassthroughRequested = Boolean(enabled);
        this._refreshTrackedWindow({emitPresentation: true, force: true});
        return this._overlayInputPassthroughApplied(this._overlayWindow);
    }

    _onBusAcquired(connection, _name) {
        this._impl = Gio.DBusExportedObject.wrapJSObject(INTERFACE_XML, this);
        this._impl.export(connection, HELPER_OBJECT_PATH);
    }

    _onNameAcquired(_connection, _name) {
    }

    _onNameLost(_connection, _name) {
        this._disconnectTrackedWindowSignals();
        this._disconnectOverlayWindowSignals();
        if (this._impl !== null) {
            this._impl.unexport();
            this._impl = null;
        }

        this._sessionToken = '';
        this._lastActiveEventJson = '';
        this._lastGeometryEventJson = '';
        this._lastPresentationEventJson = '';
        this._clearForegroundHold();
        this._stopShellChromeMaintenance();
        this._restoreShellChrome();
    }

    _emitPropertyChanged(name, value) {
        if (this._impl === null)
            return;

        this._impl.emit_property_changed(name, value);
    }

    _connectDisplaySignals() {
        if (this._display !== null)
            return;

        this._display = global.display ?? null;
        if (this._display === null)
            return;

        const focusHandler = this._onFocusWindowChanged.bind(this);
        const layoutHandler = this._onDisplayWindowsChanged.bind(this);
        const connected = this._connectSignal(this._display, 'focus-window', focusHandler);
        if (!connected)
            this._connectSignal(this._display, 'notify::focus-window', focusHandler);
        this._connectSignal(this._display, 'window-created', layoutHandler);
        this._connectSignal(this._display, 'restacked', layoutHandler);
    }

    _disconnectDisplaySignals() {
        if (this._display === null)
            return;

        for (const signalId of this._displaySignalIds) {
            try {
                this._display.disconnect(signalId);
            } catch (_error) {
            }
        }
        this._displaySignalIds = [];
        this._display = null;
    }

    _onFocusWindowChanged() {
        this._refreshTrackedWindow({emitActive: true, emitGeometry: true, emitPresentation: true});
    }

    _onDisplayWindowsChanged() {
        this._refreshTrackedWindow({emitActive: true, emitGeometry: true, emitPresentation: true});
    }

    _refreshTrackedWindow({emitActive = false, emitGeometry = false, emitPresentation = false, force = false} = {}) {
        const nextWindow = this._resolveTargetWindow();
        if (!this._sameWindow(this._trackedWindow, nextWindow))
            this._setTrackedWindow(nextWindow);
        const nextOverlayWindow = this._resolveOverlayWindow();
        if (!this._sameWindow(this._overlayWindow, nextOverlayWindow))
            this._setOverlayWindow(nextOverlayWindow);

        if (emitActive)
            this._emitActiveWindowChanged(force);
        if (emitGeometry)
            this._emitWindowGeometryChanged(force);
        if (emitPresentation)
            this._emitPresentationStateChanged(force);
    }

    _resolveTargetWindow() {
        const focusedWindow = this._resolveFocusedWindow();
        if (this._isTargetWindow(focusedWindow))
            return focusedWindow;

        if (this._isTargetWindow(this._trackedWindow))
            return this._trackedWindow;

        for (const candidate of this._listCandidateWindows()) {
            if (this._isTargetWindow(candidate))
                return candidate;
        }

        return null;
    }

    _resolveOverlayWindow() {
        const focusedWindow = this._resolveFocusedWindow();
        if (this._isOverlayWindow(focusedWindow))
            return focusedWindow;

        if (this._isOverlayWindow(this._overlayWindow))
            return this._overlayWindow;

        for (const candidate of this._listCandidateWindows()) {
            if (this._isOverlayWindow(candidate))
                return candidate;
        }

        return null;
    }

    _resolveFocusedWindow() {
        const display = this._display ?? global.display ?? null;
        if (display === null)
            return null;

        if (typeof display.get_focus_window === 'function')
            return display.get_focus_window();
        if ('focus_window' in display)
            return display.focus_window;
        return null;
    }

    _listCandidateWindows() {
        const candidates = [];
        const seenIdentifiers = new Set();
        const addWindow = window => {
            if (window === null || window === undefined)
                return;

            const identifier = this._windowIdentifier(window);
            if (identifier) {
                if (seenIdentifiers.has(identifier))
                    return;
                seenIdentifiers.add(identifier);
            }
            candidates.push(window);
        };

        const workspaceManager = global.workspace_manager ?? null;
        if (workspaceManager !== null && typeof workspaceManager.get_active_workspace === 'function') {
            const activeWorkspace = workspaceManager.get_active_workspace();
            if (activeWorkspace !== null && activeWorkspace !== undefined && typeof activeWorkspace.list_windows === 'function') {
                for (const window of activeWorkspace.list_windows())
                    addWindow(window);
            }
        }

        if (typeof global.get_window_actors === 'function') {
            for (const actor of global.get_window_actors()) {
                if (actor === null || actor === undefined)
                    continue;
                const window = actor.metaWindow ?? actor.meta_window ?? null;
                addWindow(window);
            }
        }

        return candidates;
    }

    _isTargetWindow(window) {
        if (window === null || window === undefined)
            return false;

        return TITLE_PATTERN.test(this._windowTitle(window));
    }

    _isOverlayWindow(window) {
        if (window === null || window === undefined)
            return false;

        return OVERLAY_TITLE_PATTERN.test(this._windowTitle(window));
    }

    _setTrackedWindow(window) {
        if (this._sameWindow(this._trackedWindow, window))
            return;

        this._disconnectTrackedWindowSignals();
        this._trackedWindow = window ?? null;
        this._lastGeometryEventJson = '';
        if (this._trackedWindow === null)
            return;

        const geometryHandler = this._onTrackedWindowGeometryChanged.bind(this);
        const lifecycleHandler = this._onTrackedWindowUnavailable.bind(this);
        this._connectTrackedWindowSignal('position-changed', geometryHandler);
        this._connectTrackedWindowSignal('size-changed', geometryHandler);
        this._connectTrackedWindowSignal('workspace-changed', geometryHandler);
        this._connectTrackedWindowSignal('shown', geometryHandler);
        this._connectTrackedWindowSignal('unmanaged', lifecycleHandler);
        this._connectTrackedWindowSignal('unmanaging', lifecycleHandler);
    }

    _setOverlayWindow(window) {
        if (this._sameWindow(this._overlayWindow, window))
            return;

        this._disconnectOverlayWindowSignals();
        this._overlayWindow = window ?? null;
        this._lastPresentationEventJson = '';
        if (this._overlayWindow === null)
            return;

        const changeHandler = this._onOverlayWindowChanged.bind(this);
        const lifecycleHandler = this._onOverlayWindowUnavailable.bind(this);
        this._connectOverlayWindowSignal('position-changed', changeHandler);
        this._connectOverlayWindowSignal('size-changed', changeHandler);
        this._connectOverlayWindowSignal('workspace-changed', changeHandler);
        this._connectOverlayWindowSignal('shown', changeHandler);
        this._connectOverlayWindowSignal('unmanaged', lifecycleHandler);
        this._connectOverlayWindowSignal('unmanaging', lifecycleHandler);
    }

    _disconnectTrackedWindowSignals() {
        if (this._trackedWindow !== null) {
            for (const signalId of this._trackedWindowSignalIds) {
                try {
                    this._trackedWindow.disconnect(signalId);
                } catch (_error) {
                }
            }
        }

        this._trackedWindowSignalIds = [];
        this._trackedWindow = null;
    }

    _disconnectOverlayWindowSignals() {
        if (this._overlayWindow !== null) {
            for (const signalId of this._overlayWindowSignalIds) {
                try {
                    this._overlayWindow.disconnect(signalId);
                } catch (_error) {
                }
            }
        }

        this._overlayWindowSignalIds = [];
        this._overlayWindow = null;
    }

    _connectTrackedWindowSignal(name, handler) {
        if (this._trackedWindow === null)
            return;

        const signalId = this._connectSignal(this._trackedWindow, name, handler);
        if (signalId !== 0)
            this._trackedWindowSignalIds.push(signalId);
    }

    _connectOverlayWindowSignal(name, handler) {
        if (this._overlayWindow === null)
            return;

        const signalId = this._connectSignal(this._overlayWindow, name, handler);
        if (signalId !== 0)
            this._overlayWindowSignalIds.push(signalId);
    }

    _connectSignal(source, name, handler) {
        try {
            const signalId = source.connect(name, handler);
            this._displaySignalIds = source === this._display ? [...this._displaySignalIds, signalId] : this._displaySignalIds;
            return signalId;
        } catch (_error) {
            return 0;
        }
    }

    _onTrackedWindowGeometryChanged() {
        this._refreshTrackedWindow({emitActive: true, emitGeometry: true, emitPresentation: true});
    }

    _onTrackedWindowUnavailable() {
        this._disconnectTrackedWindowSignals();
        this._lastActiveEventJson = '';
        this._lastGeometryEventJson = '';
        this._lastPresentationEventJson = '';
        this._clearForegroundHold();
        this._emitActiveWindowChanged(true);
        this._emitPresentationStateChanged(true);
    }

    _onOverlayWindowChanged() {
        this._refreshTrackedWindow({emitPresentation: true});
    }

    _onOverlayWindowUnavailable() {
        this._disconnectOverlayWindowSignals();
        this._lastPresentationEventJson = '';
        this._emitPresentationStateChanged(true);
    }

    _emitActiveWindowChanged(force) {
        const payload = this._buildActiveWindowPayload();
        this._emitEvent('active_window_changed', payload, {
            cacheSlot: '_lastActiveEventJson',
            force,
        });
    }

    _emitWindowGeometryChanged(force) {
        if (this._trackedWindow === null)
            return;

        const payload = this._buildWindowGeometryPayload();
        if (payload === null)
            return;

        this._emitEvent('window_geometry_changed', payload, {
            cacheSlot: '_lastGeometryEventJson',
            force,
        });
    }

    _emitPresentationStateChanged(force) {
        const payload = this._buildPresentationStatePayload();
        const shouldPromote = payload.target_found && payload.overlay_found && payload.target_is_foreground && payload.target_is_visible;
        if (shouldPromote)
            payload.promotion_applied = this._promoteOverlayWindow();
        else
            this._relaxOverlayWindow();

        payload.overlay_input_passthrough_applied = this._applyOverlayInputPassthrough(
            this._overlayWindow,
            this._overlayInputPassthroughRequested);
        this._updateShellChromeVisibility(shouldPromote);
        payload.overlay_actor_reactive = this._overlayActorReactive(this._overlayWindow);
        payload.overlay_is_above = this._windowIsAbove(this._overlayWindow);
        payload.shell_chrome_hidden = this._shellChromeHidden;
        payload.panel_hidden = this._panelChromeHidden();
        payload.dock_hidden = this._dockChromeHidden();
        this._emitEvent('presentation_state_changed', payload, {
            cacheSlot: '_lastPresentationEventJson',
            force,
        });
    }

    _buildActiveWindowPayload() {
        if (this._trackedWindow === null) {
            return {
                matched: false,
                identifier: '',
                title: '',
                wm_class: '',
                is_foreground: false,
                is_visible: false,
            };
        }

        return {
            matched: true,
            identifier: this._windowIdentifier(this._trackedWindow),
            title: this._windowTitle(this._trackedWindow),
            wm_class: this._windowWmClass(this._trackedWindow),
            is_foreground: this._windowIsFocused(this._trackedWindow),
            is_visible: this._windowIsVisible(this._trackedWindow),
        };
    }

    _buildWindowGeometryPayload() {
        if (this._trackedWindow === null)
            return null;

        const rect = this._windowFrameRect(this._trackedWindow);
        if (rect === null)
            return null;

        return {
            identifier: this._windowIdentifier(this._trackedWindow),
            title: this._windowTitle(this._trackedWindow),
            wm_class: this._windowWmClass(this._trackedWindow),
            is_foreground: this._windowIsFocused(this._trackedWindow),
            is_visible: this._windowIsVisible(this._trackedWindow),
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height,
        };
    }

    _buildPresentationStatePayload() {
        const trackedWindow = this._trackedWindow;
        const overlayWindow = this._overlayWindow;
        return {
            target_found: trackedWindow !== null,
            target_identifier: this._windowIdentifier(trackedWindow),
            target_title: this._windowTitle(trackedWindow),
            target_is_foreground: this._windowIsFocused(trackedWindow),
            target_is_visible: this._windowIsVisible(trackedWindow),
            overlay_found: overlayWindow !== null,
            overlay_identifier: this._windowIdentifier(overlayWindow),
            overlay_title: this._windowTitle(overlayWindow),
            overlay_wm_class: this._windowWmClass(overlayWindow),
            overlay_is_visible: this._windowIsVisible(overlayWindow),
            overlay_is_above: this._windowIsAbove(overlayWindow),
            overlay_input_passthrough_requested: this._overlayInputPassthroughRequested,
            overlay_input_passthrough_applied: this._overlayInputPassthroughApplied(overlayWindow),
            overlay_actor_reactive: this._overlayActorReactive(overlayWindow),
            shell_chrome_hidden: this._shellChromeHidden,
            panel_hidden: this._panelChromeHidden(),
            dock_hidden: this._dockChromeHidden(),
            promotion_applied: false,
        };
    }

    _emitEvent(eventName, payload, {cacheSlot, force = false} = {}) {
        if (!this.SessionReady || this._impl === null)
            return;

        const messageJson = JSON.stringify({
            type: 'event',
            helper_kind: HELPER_KIND,
            protocol_version: HELPER_PROTOCOL_VERSION,
            session_token: this._sessionToken,
            event: eventName,
            payload,
        });
        if (!force && cacheSlot && this[cacheSlot] === messageJson)
            return;

        if (cacheSlot)
            this[cacheSlot] = messageJson;
        this._impl.emit_signal('Event', new GLib.Variant('(s)', [messageJson]));
    }

    _sameWindow(left, right) {
        return this._windowIdentifier(left) === this._windowIdentifier(right);
    }

    _windowIdentifier(window) {
        if (window === null || window === undefined)
            return '';

        const stableSequence = this._callNumber(window, 'get_stable_sequence');
        if (stableSequence !== null)
            return `stable:${stableSequence}`;
        const windowId = this._callNumber(window, 'get_id');
        if (windowId !== null)
            return `id:${windowId}`;
        return this._uuid ? `uuid:${this._uuid}:tracked` : 'tracked-window';
    }

    _windowTitle(window) {
        return this._callString(window, 'get_title');
    }

    _windowWmClass(window) {
        return this._callString(window, 'get_wm_class');
    }

    _windowIsVisible(window) {
        const rect = this._windowFrameRect(window);
        if (rect === null || rect.width <= 0 || rect.height <= 0)
            return false;

        try {
            if (typeof window.is_hidden === 'function')
                return !window.is_hidden();
        } catch (_error) {
        }
        return true;
    }

    _windowFrameRect(window) {
        if (window === null || window === undefined)
            return null;

        try {
            const rect = window.get_frame_rect();
            if (rect === null || rect === undefined)
                return null;
            return {
                x: Number(rect.x ?? 0),
                y: Number(rect.y ?? 0),
                width: Number(rect.width ?? 0),
                height: Number(rect.height ?? 0),
            };
        } catch (_error) {
            return null;
        }
    }

    _windowIsAbove(window) {
        if (window === null || window === undefined)
            return false;

        try {
            if (typeof window.is_above === 'function')
                return Boolean(window.is_above());
        } catch (_error) {
        }

        try {
            if ('above' in window)
                return Boolean(window.above);
        } catch (_error) {
        }

        return false;
    }

    _windowIsFocused(window) {
        if (window === null || window === undefined)
            return false;

        const identifier = this._windowIdentifier(window);
        const nowMs = this._monotonicTimeMs();
        const focusState = this._windowFocusState(window);

        if (focusState === 'focused') {
            this._rememberForeground(identifier, nowMs);
            return true;
        }

        if (this._shouldHoldForeground(identifier, nowMs) && this._windowIsVisible(window))
            return true;

        return false;
    }

    _windowFocusState(window) {
        if (window === null || window === undefined)
            return 'background';

        const directFocus = this._windowDirectFocusState(window);
        if (directFocus === true)
            return 'focused';

        const focusedWindow = this._resolveFocusedWindow();
        if (focusedWindow !== null && focusedWindow !== undefined)
            return this._sameWindow(window, focusedWindow) ? 'focused' : 'background';

        return directFocus === false ? 'unknown' : 'unknown';
    }

    _windowDirectFocusState(window) {
        try {
            if (typeof window.has_focus === 'function')
                return Boolean(window.has_focus());
        } catch (_error) {
        }

        try {
            if (typeof window.appears_focused === 'function')
                return Boolean(window.appears_focused());
        } catch (_error) {
        }

        try {
            if ('appears_focused' in window)
                return Boolean(window.appears_focused);
        } catch (_error) {
        }

        return null;
    }

    _rememberForeground(identifier, nowMs) {
        if (!identifier)
            return;

        this._lastForegroundWindowId = identifier;
        this._lastForegroundTimestampMs = nowMs;
    }

    _shouldHoldForeground(identifier, nowMs) {
        if (!identifier || this._lastForegroundWindowId !== identifier)
            return false;

        return (nowMs - this._lastForegroundTimestampMs) < FOREGROUND_LOSS_HOLD_MS;
    }

    _clearForegroundHold() {
        this._lastForegroundWindowId = '';
        this._lastForegroundTimestampMs = 0;
    }

    _promoteOverlayWindow() {
        if (this._overlayWindow === null || this._trackedWindow === null)
            return false;

        let attempted = false;

        if (typeof this._overlayWindow.make_above === 'function') {
            try {
                this._overlayWindow.make_above();
                attempted = true;
            } catch (_error) {
            }
        }

        if (typeof this._overlayWindow.raise === 'function') {
            try {
                this._overlayWindow.raise();
                attempted = true;
            } catch (_error) {
            }
        }

        return this._windowIsAbove(this._overlayWindow) || attempted;
    }

    _relaxOverlayWindow() {
        if (this._overlayWindow === null)
            return;

        if (typeof this._overlayWindow.unmake_above !== 'function')
            return;

        try {
            this._overlayWindow.unmake_above();
        } catch (_error) {
        }
    }

    _updateShellChromeVisibility(shouldHide) {
        if (shouldHide) {
            this._hideShellChrome();
            this._ensureShellChromeMaintenance();
        } else {
            this._stopShellChromeMaintenance();
            this._restoreShellChrome();
        }
    }

    _hideShellChrome() {
        const panelActors = this._panelChromeActors();
        const dockActors = this._dockActors();
        if (!panelActors.length && !dockActors.length) {
            this._shellChromeHidden = false;
            return;
        }

        this._panelChromeState = this._mergeChromeState(this._panelChromeState, panelActors);
        this._dockChromeState = this._mergeDockChromeState(this._dockChromeState, dockActors);

        for (const state of this._panelChromeState) {
            if (!this._actorVisible(state.actor))
                continue;
            this._setActorVisible(state.actor, false);
        }
        for (const state of this._dockChromeState)
            this._hideDockActor(state);

        this._shellChromeHidden =
            this._allActorsHidden(this._panelChromeActors()) &&
            this._allActorsHidden(this._dockActors());
    }

    _restoreShellChrome() {
        for (const state of this._panelChromeState) {
            if (!state.wasVisible)
                continue;
            this._setActorVisible(state.actor, true);
        }
        for (const state of this._dockChromeState)
            this._restoreDockActor(state);

        this._panelChromeState = [];
        this._dockChromeState = [];
        this._shellChromeHidden = false;
    }

    _panelChromeActors() {
        const actors = [];
        const panelBox = Main.layoutManager?.panelBox ?? null;
        if (panelBox !== null && panelBox !== undefined)
            actors.push(panelBox);
        const panel = Main.panel ?? null;
        if (panel !== null && panel !== undefined)
            actors.push(panel);
        const leftCorner = Main.panel?._leftCorner ?? null;
        if (leftCorner !== null && leftCorner !== undefined)
            actors.push(leftCorner);
        const rightCorner = Main.panel?._rightCorner ?? null;
        if (rightCorner !== null && rightCorner !== undefined)
            actors.push(rightCorner);
        return actors;
    }

    _dockActors() {
        const root = global.stage ?? null;
        if (root === null)
            return [];

        const actors = [];
        this._collectNamedActors(root, 'dashtodockContainer', actors);
        return actors;
    }

    _collectNamedActors(actor, targetName, matches) {
        if (actor === null || actor === undefined)
            return;

        if (this._actorName(actor) === targetName)
            matches.push(actor);

        if (typeof actor.get_children !== 'function')
            return;

        let children = [];
        try {
            children = actor.get_children() ?? [];
        } catch (_error) {
            children = [];
        }

        for (const child of children)
            this._collectNamedActors(child, targetName, matches);
    }

    _panelChromeHidden() {
        const actors = this._panelChromeActors();
        return actors.length > 0 && actors.every(actor => !this._actorVisible(actor));
    }

    _dockChromeHidden() {
        const actors = this._dockActors();
        return actors.length > 0 && actors.every(actor => !this._actorVisible(actor));
    }

    _allActorsHidden(actors) {
        return actors.every(actor => !this._actorVisible(actor));
    }

    _mergeChromeState(existingState, actors) {
        const merged = [];
        for (const actor of actors) {
            const existing = existingState.find(state => state.actor === actor) ?? null;
            if (existing !== null) {
                merged.push(existing);
                continue;
            }
            merged.push({
                actor,
                wasVisible: this._actorVisible(actor),
            });
        }
        return merged;
    }

    _mergeDockChromeState(existingState, actors) {
        const merged = [];
        for (const actor of actors) {
            const existing = existingState.find(state => state.actor === actor) ?? null;
            if (existing !== null) {
                merged.push(existing);
                continue;
            }
            merged.push(this._captureDockChromeState(actor));
        }
        return merged;
    }

    _captureDockChromeState(actor) {
        const box = actor?._box ?? null;
        return {
            actor,
            wasVisible: this._actorVisible(actor),
            ignoreHover: this._readProperty(actor, '_ignoreHover'),
            autohideIsEnabled: this._readProperty(actor, '_autohideIsEnabled'),
            intellihideIsEnabled: this._readProperty(actor, '_intellihideIsEnabled'),
            boxReactive: this._actorReactive(box),
        };
    }

    _actorName(actor) {
        if (actor === null || actor === undefined)
            return '';

        try {
            if (typeof actor.get_name === 'function')
                return String(actor.get_name() ?? '').trim();
        } catch (_error) {
        }

        try {
            if ('name' in actor)
                return String(actor.name ?? '').trim();
        } catch (_error) {
        }

        return '';
    }

    _actorVisible(actor) {
        if (actor === null || actor === undefined)
            return false;

        try {
            if (typeof actor.is_visible === 'function')
                return Boolean(actor.is_visible());
        } catch (_error) {
        }

        try {
            if ('visible' in actor)
                return Boolean(actor.visible);
        } catch (_error) {
        }

        return false;
    }

    _actorReactive(actor) {
        if (actor === null || actor === undefined)
            return null;

        try {
            if (typeof actor.get_reactive === 'function')
                return Boolean(actor.get_reactive());
        } catch (_error) {
        }

        try {
            if ('reactive' in actor)
                return Boolean(actor.reactive);
        } catch (_error) {
        }

        return null;
    }

    _setActorReactive(actor, reactive) {
        if (actor === null || actor === undefined || reactive === null)
            return;

        try {
            if (typeof actor.set_reactive === 'function') {
                actor.set_reactive(Boolean(reactive));
                return;
            }
        } catch (_error) {
        }

        try {
            if ('reactive' in actor)
                actor.reactive = Boolean(reactive);
        } catch (_error) {
        }
    }

    _readProperty(actor, propertyName) {
        if (actor === null || actor === undefined)
            return null;

        try {
            if (propertyName in actor)
                return actor[propertyName];
        } catch (_error) {
        }

        return null;
    }

    _setActorVisible(actor, visible) {
        if (actor === null || actor === undefined)
            return;

        try {
            if (!visible && typeof actor._hide === 'function') {
                actor._hide();
                return;
            }
            if (visible && typeof actor._show === 'function') {
                actor._show();
                return;
            }
        } catch (_error) {
        }

        try {
            if (visible && typeof actor.show === 'function') {
                actor.show();
                return;
            }
            if (!visible && typeof actor.hide === 'function') {
                actor.hide();
                return;
            }
        } catch (_error) {
        }

        try {
            if ('visible' in actor)
                actor.visible = Boolean(visible);
        } catch (_error) {
        }
    }

    _hideDockActor(state) {
        const actor = state?.actor ?? null;
        if (actor === null)
            return;

        try {
            if ('_ignoreHover' in actor)
                actor._ignoreHover = true;
        } catch (_error) {
        }
        try {
            if ('_autohideIsEnabled' in actor)
                actor._autohideIsEnabled = false;
        } catch (_error) {
        }
        try {
            if ('_intellihideIsEnabled' in actor)
                actor._intellihideIsEnabled = false;
        } catch (_error) {
        }
        try {
            if (actor._intellihide !== null && actor._intellihide !== undefined &&
                typeof actor._intellihide.disable === 'function')
                actor._intellihide.disable();
        } catch (_error) {
        }

        const box = actor._box ?? null;
        this._setActorReactive(box, false);
        try {
            if (box !== null && typeof box.sync_hover === 'function')
                box.sync_hover();
        } catch (_error) {
        }

        try {
            if (typeof actor._removeAnimations === 'function')
                actor._removeAnimations();
        } catch (_error) {
        }
        try {
            if (typeof actor._animateOut === 'function') {
                actor._animateOut(0, 0);
                return;
            }
        } catch (_error) {
        }

        this._setActorVisible(actor, false);
    }

    _restoreDockActor(state) {
        const actor = state?.actor ?? null;
        if (actor === null)
            return;

        try {
            if (state.ignoreHover !== null && '_ignoreHover' in actor)
                actor._ignoreHover = Boolean(state.ignoreHover);
        } catch (_error) {
        }
        try {
            if (state.autohideIsEnabled !== null && '_autohideIsEnabled' in actor)
                actor._autohideIsEnabled = Boolean(state.autohideIsEnabled);
        } catch (_error) {
        }
        try {
            if (state.intellihideIsEnabled !== null && '_intellihideIsEnabled' in actor)
                actor._intellihideIsEnabled = Boolean(state.intellihideIsEnabled);
        } catch (_error) {
        }
        try {
            if (state.intellihideIsEnabled !== null &&
                actor._intellihide !== null &&
                actor._intellihide !== undefined) {
                if (state.intellihideIsEnabled)
                    actor._intellihide.enable();
                else if (typeof actor._intellihide.disable === 'function')
                    actor._intellihide.disable();
            }
        } catch (_error) {
        }

        const box = actor._box ?? null;
        this._setActorReactive(box, state.boxReactive);
        try {
            if (box !== null && typeof box.sync_hover === 'function')
                box.sync_hover();
        } catch (_error) {
        }

        try {
            if (typeof actor._updateVisibilityMode === 'function') {
                actor._updateVisibilityMode();
                return;
            }
        } catch (_error) {
        }

        if (state.wasVisible)
            this._setActorVisible(actor, true);
        else
            this._setActorVisible(actor, false);
    }

    _ensureShellChromeMaintenance() {
        if (this._shellChromeMaintenanceSourceId !== 0)
            return;

        this._shellChromeMaintenanceSourceId = GLib.timeout_add(
            GLib.PRIORITY_DEFAULT,
            SHELL_CHROME_REAPPLY_MS,
            () => {
                if (!this._shouldMaintainShellChrome()) {
                    this._shellChromeMaintenanceSourceId = 0;
                    this._restoreShellChrome();
                    return GLib.SOURCE_REMOVE;
                }

                this._hideShellChrome();
                return GLib.SOURCE_CONTINUE;
            });
    }

    _stopShellChromeMaintenance() {
        if (this._shellChromeMaintenanceSourceId === 0)
            return;

        try {
            GLib.Source.remove(this._shellChromeMaintenanceSourceId);
        } catch (_error) {
        }
        this._shellChromeMaintenanceSourceId = 0;
    }

    _shouldMaintainShellChrome() {
        return this._trackedWindow !== null &&
            this._overlayWindow !== null &&
            this._windowIsVisible(this._trackedWindow) &&
            this._windowIsFocused(this._trackedWindow);
    }

    _applyOverlayInputPassthrough(window, enabled) {
        const actor = this._windowActor(window);
        if (actor === null)
            return false;

        const reactive = !Boolean(enabled);
        let attempted = false;

        try {
            if (typeof actor.set_reactive === 'function') {
                actor.set_reactive(reactive);
                attempted = true;
            } else if ('reactive' in actor) {
                actor.reactive = reactive;
                attempted = true;
            }
        } catch (_error) {
        }

        try {
            if (typeof actor.set_can_focus === 'function')
                actor.set_can_focus(reactive);
        } catch (_error) {
        }

        const child = typeof actor.get_first_child === 'function' ? actor.get_first_child() : null;
        if (child !== null && child !== undefined) {
            try {
                if (typeof child.set_reactive === 'function')
                    child.set_reactive(reactive);
                else if ('reactive' in child)
                    child.reactive = reactive;
            } catch (_error) {
            }
        }

        return this._overlayInputPassthroughApplied(window) || attempted;
    }

    _overlayInputPassthroughApplied(window) {
        if (window === null || window === undefined)
            return false;

        const actorReactive = this._overlayActorReactive(window);
        return actorReactive === false;
    }

    _overlayActorReactive(window) {
        const actor = this._windowActor(window);
        if (actor === null)
            return null;

        try {
            if (typeof actor.get_reactive === 'function')
                return Boolean(actor.get_reactive());
        } catch (_error) {
        }

        try {
            if ('reactive' in actor)
                return Boolean(actor.reactive);
        } catch (_error) {
        }

        return null;
    }

    _windowActor(window) {
        if (window === null || window === undefined)
            return null;

        try {
            if (typeof window.get_compositor_private === 'function')
                return window.get_compositor_private();
        } catch (_error) {
        }

        if (typeof global.get_window_actors !== 'function')
            return null;

        for (const actor of global.get_window_actors()) {
            if (actor === null || actor === undefined)
                continue;
            const actorWindow = actor.metaWindow ?? actor.meta_window ?? null;
            if (this._sameWindow(window, actorWindow))
                return actor;
        }

        return null;
    }

    _monotonicTimeMs() {
        try {
            return Math.floor(GLib.get_monotonic_time() / 1000);
        } catch (_error) {
            return 0;
        }
    }

    _callString(target, methodName) {
        if (target === null || target === undefined)
            return '';
        if (typeof target[methodName] !== 'function')
            return '';

        try {
            return String(target[methodName]() ?? '').trim();
        } catch (_error) {
            return '';
        }
    }

    _callNumber(target, methodName) {
        if (target === null || target === undefined)
            return null;
        if (typeof target[methodName] !== 'function')
            return null;

        try {
            const value = Number(target[methodName]());
            return Number.isFinite(value) ? value : null;
        } catch (_error) {
            return null;
        }
    }

}
