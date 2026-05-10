import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import {EDMCModernOverlayHelperService} from './service.js';

export default class EDMCModernOverlayExtension extends Extension {
    enable() {
        this._helperService = new EDMCModernOverlayHelperService({
            uuid: this.uuid,
        });
        this._helperService.enable();
    }

    disable() {
        this._helperService?.disable();
        this._helperService = null;
    }
}
