export const HELPER_UUID = 'edmc-modern-overlay-helper@edmcmodernoverlay.github.io';
export const HELPER_KIND = 'gnome_shell_extension';
export const HELPER_PROTOCOL = 3;
export const HELPER_VERSION = '1.0.0';
export const HELPER_DBUS_SERVICE = 'org.edmc.ModernOverlay.Helper';
export const HELPER_DBUS_OBJECT_PATH = '/org/edmc/ModernOverlay/Helper';
export const HELPER_DBUS_INTERFACE = 'org.edmc.ModernOverlay.Helper';
export const HELPER_DBUS_HELLO_METHOD = 'Hello';
export const HELPER_DBUS_HEALTH_METHOD = 'GetHealth';
export const HELPER_DBUS_TARGET_METHOD = 'GetTargetState';
export const HELPER_DBUS_PRESENTATION_METHOD = 'ApplyPresentation';
export const HELPER_COORDINATE_SPACE = 'gnome_shell_global_logical';
export const HELPER_DEV_MODE_CONFIG_DIR = 'EDMCModernOverlay';
export const HELPER_DEV_MODE_CONFIG_FILE = 'gnome_helper_dev_mode.json';
export const HELPER_DEV_MODE_DEFAULT = 'full_helper';
export const HELPER_DEV_MODE_NAMES = Object.freeze([
    'lifecycle_only',
    'dbus_health_only',
    'target_query_enabled',
    'overview_hooks_enabled',
    'raster_code_enabled_no_actor',
    'raster_actor_enabled',
    'full_helper',
]);
export const HELPER_CAPABILITIES = Object.freeze([
    'hello',
    'health',
    'version',
    'protocol',
    'capabilities',
    'target_state',
    'presentation_state',
]);
