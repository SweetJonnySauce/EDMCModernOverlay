import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';

import {
    HELPER_KIND,
    HELPER_PROTOCOL,
    HELPER_UUID,
    HELPER_VERSION,
} from './constants.js';

export default class EdmcModernOverlayHelperExtension extends Extension {
    enable() {
        this._helperIdentity = {
            uuid: HELPER_UUID,
            helperKind: HELPER_KIND,
            helperProtocol: HELPER_PROTOCOL,
            helperVersion: HELPER_VERSION,
        };
    }

    disable() {
        this._helperIdentity = null;
    }
}
