import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';

import {
    HELPER_CAPABILITIES,
    HELPER_DBUS_HEALTH_METHOD,
    HELPER_DBUS_HELLO_METHOD,
    HELPER_DBUS_INTERFACE,
    HELPER_DBUS_OBJECT_PATH,
    HELPER_DBUS_SERVICE,
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
  </interface>
</node>`;

class HelperHealthService {
    constructor() {
        this._startedAtUnixMs = Date.now();
        this._startedAtMonotonicUs = GLib.get_monotonic_time();
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
