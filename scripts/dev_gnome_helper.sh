#!/usr/bin/env bash

# Development helper for installing/removing the GNOME Shell helper from a
# source checkout. This intentionally does not run the full Linux installer.

set -euo pipefail
IFS=$'\n\t'

readonly SCRIPT_PATH="${BASH_SOURCE[0]}"
readonly SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly HELPER_UUID="edmc-modern-overlay-helper@edmcmodernoverlay.github.io"
readonly HELPER_SOURCE_DIR="${REPO_ROOT}/helpers/gnome_shell_extension"
readonly HELPER_DBUS_SERVICE="org.edmc.ModernOverlay.Helper"
readonly HELPER_DBUS_OBJECT_PATH="/org/edmc/ModernOverlay/Helper"
readonly HELPER_DBUS_INTERFACE="org.edmc.ModernOverlay.Helper"
readonly HELPER_DBUS_HEALTH_METHOD="GetHealth"

ACTION="status"
ASSUME_YES=false
DRY_RUN=false
FORCE_SESSION=false
NO_ENABLE=false

usage() {
    cat <<'EOF'
Usage: dev_gnome_helper.sh <install|update|reload|enable|disable|uninstall|status> [options]

Install or remove the EDMC Modern Overlay GNOME Shell helper from a source
checkout for local development.

Actions:
  install       Copy helper source to the user-local GNOME extension path and enable it.
  update        Same as install; clean-replaces the installed helper directory first.
  reload        Disable, remove, reinstall, enable, and print status.
  enable        Enable an already installed/discovered helper extension.
  disable       Disable the helper extension, but leave files installed.
  uninstall     Disable the helper extension and remove only the helper UUID directory.
  status        Print extension discovery, enablement, global-user-extension, and DBus health.

Options:
  -y, --yes         Automatically approve install/update/enable/disable/uninstall prompts.
      --dry-run     Print actions without copying, enabling, disabling, or removing.
      --force       Allow install/update outside an obvious GNOME Wayland session.
      --no-enable   Copy files during install/update but do not call gnome-extensions enable.
  -h, --help        Show this message.

Notes:
  - No sudo is used.
  - MODERN_OVERLAY_GNOME_HELPER_EXTENSION_BASE overrides the install base.
  - When run from a Snap-confined terminal, the script uses SNAP_REAL_HOME or
    the account home directory so the helper installs into the real user's
    GNOME Shell extension directory, not the Snap-private data directory.
  - Log out and log back in after install/update/uninstall, or when status
    remains inactive/not discovered. Enabling an already discovered helper can
    be trusted immediately when GNOME reports ACTIVE and DBus health responds.
EOF
}

die() {
    printf 'dev_gnome_helper.sh: %s\n' "$1" >&2
    exit 1
}

warn() {
    printf 'warning: %s\n' "$1" >&2
}

info() {
    printf '%s\n' "$1"
}

lower() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

parse_args() {
    local action_seen=false
    while (($# > 0)); do
        case "$1" in
            install|update|reload|enable|disable|uninstall|status)
                if [[ "$action_seen" == true ]]; then
                    die "multiple actions supplied"
                fi
                ACTION="$1"
                action_seen=true
                ;;
            -y|--yes|--assume-yes)
                ASSUME_YES=true
                ;;
            --dry-run)
                DRY_RUN=true
                ;;
            --force)
                FORCE_SESSION=true
                ;;
            --no-enable)
                NO_ENABLE=true
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                die "unknown argument: $1"
                ;;
        esac
        shift
    done
}

path_is_snap_private() {
    local path="$1"
    [[ "$path" == */snap/* ]]
}

snap_confined_environment() {
    [[ -n "${SNAP:-}" ]] && return 0
    path_is_snap_private "${HOME:-}" && return 0
    path_is_snap_private "${XDG_DATA_HOME:-}" && return 0
    return 1
}

account_home() {
    if [[ -n "${SNAP_REAL_HOME:-}" ]]; then
        printf '%s' "$SNAP_REAL_HOME"
        return
    fi
    local username passwd_home
    username="$(id -un 2>/dev/null || true)"
    if [[ -n "$username" ]] && command -v getent >/dev/null 2>&1; then
        passwd_home="$(getent passwd "$username" 2>/dev/null | cut -d: -f6 || true)"
        if [[ -n "$passwd_home" ]] && ! path_is_snap_private "$passwd_home"; then
            printf '%s' "$passwd_home"
            return
        fi
    fi
    if [[ -n "${USER:-}" && -d "/home/${USER}" ]]; then
        printf '/home/%s' "$USER"
        return
    fi
    printf '%s' "$HOME"
}

host_data_home() {
    if snap_confined_environment; then
        printf '%s/.local/share' "$(account_home)"
        return
    fi
    if [[ -n "${XDG_DATA_HOME:-}" ]]; then
        printf '%s' "$XDG_DATA_HOME"
        return
    fi
    printf '%s/.local/share' "$HOME"
}

extension_base_dir() {
    if [[ -n "${MODERN_OVERLAY_GNOME_HELPER_EXTENSION_BASE:-}" ]]; then
        printf '%s' "$MODERN_OVERLAY_GNOME_HELPER_EXTENSION_BASE"
        return
    fi
    printf '%s/gnome-shell/extensions' "$(host_data_home)"
}

install_dir() {
    printf '%s/%s' "$(extension_base_dir)" "$HELPER_UUID"
}

require_command() {
    local name="$1"
    command -v "$name" >/dev/null 2>&1 || die "required command not found: $name"
}

session_is_gnome_wayland() {
    local session desktop
    session="$(lower "${XDG_SESSION_TYPE:-}")"
    desktop="$(lower "${XDG_CURRENT_DESKTOP:-},${DESKTOP_SESSION:-}")"
    [[ "$session" == "wayland" && ( "$desktop" == *"gnome"* || "$desktop" == *"ubuntu"* ) ]]
}

check_session_for_mutation() {
    if session_is_gnome_wayland; then
        return
    fi
    if [[ "$FORCE_SESSION" == true ]]; then
        warn "continuing outside an obvious GNOME Wayland session because --force was supplied"
        return
    fi
    die "install/update should be run from GNOME Wayland; use --force only for deliberate development testing"
}

check_source_dir() {
    [[ -d "$HELPER_SOURCE_DIR" ]] || die "helper source directory missing: $HELPER_SOURCE_DIR"
    [[ -f "$HELPER_SOURCE_DIR/metadata.json" ]] || die "helper metadata missing: $HELPER_SOURCE_DIR/metadata.json"
    [[ -f "$HELPER_SOURCE_DIR/extension.js" ]] || die "helper extension source missing: $HELPER_SOURCE_DIR/extension.js"
}

session_bus_available() {
    [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" || -S "${XDG_RUNTIME_DIR:-}/bus" ]]
}

check_common_prerequisites() {
    require_command gnome-extensions
    require_command gdbus
    require_command gsettings
    session_bus_available || die "DBus session bus not available"
}

check_install_prerequisites() {
    check_source_dir
    check_common_prerequisites
    require_command gjs
}

prompt_yes_no_default_no() {
    local prompt="$1"
    if [[ "$ASSUME_YES" == true ]]; then
        printf '%s [y/N]: y\n' "$prompt"
        return 0
    fi
    if [[ ! -t 0 ]]; then
        printf '%s [y/N]: n (non-interactive)\n' "$prompt"
        return 1
    fi
    local response
    printf '%s [y/N]: ' "$prompt"
    read -r response || return 1
    case "${response:-}" in
        [Yy]|[Yy][Ee][Ss])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

safe_remove_install_dir() {
    local base target
    base="$(extension_base_dir)"
    target="$(install_dir)"
    [[ "$(basename "$target")" == "$HELPER_UUID" ]] || die "refusing to remove unexpected path: $target"
    [[ "$target" == "$base/$HELPER_UUID" ]] || die "refusing to remove path outside extension base: $target"
    if [[ "$DRY_RUN" == true ]]; then
        info "[dry-run] Would remove $target"
        return
    fi
    rm -rf -- "$target"
}

copy_source_to_install_dir() {
    local base target
    base="$(extension_base_dir)"
    target="$(install_dir)"
    if [[ "$DRY_RUN" == true ]]; then
        info "[dry-run] Would create $base"
        info "[dry-run] Would clean-replace $target from $HELPER_SOURCE_DIR"
        return
    fi
    mkdir -p "$base"
    safe_remove_install_dir
    mkdir -p "$target"
    cp -a "$HELPER_SOURCE_DIR"/. "$target"/
}

global_user_extensions_disabled() {
    local value
    value="$(gsettings get org.gnome.shell disable-user-extensions 2>/dev/null || true)"
    [[ "$(lower "$value")" == "true" ]]
}

print_global_disabled_remediation() {
    cat <<'EOF'
GNOME user extensions are globally disabled.
Run this yourself if you want to enable user extensions, then log out and back in:

  gsettings set org.gnome.shell disable-user-extensions false
EOF
}

extension_info() {
    gnome-extensions info "$HELPER_UUID" 2>&1
}

extension_info_field() {
    local text="$1"
    local key="$2"
    printf '%s\n' "$text" | awk -F': *' -v key="$key" '
        {
            label = $1
            gsub(/^[ \t]+|[ \t]+$/, "", label)
            if (label == key) {
                print $2
                exit
            }
        }
    '
}

enable_extension() {
    if [[ "$DRY_RUN" == true ]]; then
        info "[dry-run] Would enable $HELPER_UUID"
        return 0
    fi
    gnome-extensions enable "$HELPER_UUID"
}

disable_extension() {
    if [[ "$DRY_RUN" == true ]]; then
        info "[dry-run] Would disable $HELPER_UUID"
        return 0
    fi
    gnome-extensions disable "$HELPER_UUID" >/dev/null 2>&1 || true
}

print_logout_required() {
    local action="$1"
    cat <<EOF
Log out and log back in before trusting final GNOME Shell helper state after ${action}.
After logging back in, run:

  $SCRIPT_PATH status
EOF
}

dbus_health_available() {
    command -v gdbus >/dev/null 2>&1 || return 1
    session_bus_available || return 1
    gdbus call --session \
        --dest "$HELPER_DBUS_SERVICE" \
        --object-path "$HELPER_DBUS_OBJECT_PATH" \
        --method "${HELPER_DBUS_INTERFACE}.${HELPER_DBUS_HEALTH_METHOD}" >/dev/null 2>&1
}

print_enable_followup() {
    local ext_info enabled shell_state
    if ! ext_info="$(extension_info)"; then
        print_logout_required "enable"
        return
    fi
    enabled="$(extension_info_field "$ext_info" "Enabled")"
    shell_state="$(extension_info_field "$ext_info" "State")"
    if [[ "$(lower "$enabled")" == "yes" && "$(lower "$shell_state")" == "active" ]] && dbus_health_available; then
        cat <<EOF
GNOME helper is ACTIVE and DBus health responded. Logout/login is not required for this enable step.
Run status any time to recheck:

  $SCRIPT_PATH status
EOF
        return
    fi
    print_logout_required "enable"
}

run_status() {
    local target
    target="$(install_dir)"
    info "GNOME helper UUID: $HELPER_UUID"
    info "Source path: $HELPER_SOURCE_DIR"
    info "Install path: $target"
    info "Session type: ${XDG_SESSION_TYPE:-unknown}"
    info "Desktop: ${XDG_CURRENT_DESKTOP:-${DESKTOP_SESSION:-unknown}}"
    if snap_confined_environment && [[ -z "${MODERN_OVERLAY_GNOME_HELPER_EXTENSION_BASE:-}" ]]; then
        info "Snap confined terminal detected: using host data home $(host_data_home)"
    fi
    if session_is_gnome_wayland; then
        info "Session check: gnome_wayland"
    else
        info "Session check: not_gnome_wayland"
    fi

    if ! command -v gnome-extensions >/dev/null 2>&1; then
        info "Extension discovery: unavailable (gnome-extensions missing)"
        return
    fi

    if [[ -d "$target" ]]; then
        info "Files installed: true"
    else
        info "Files installed: false"
    fi

    if command -v gsettings >/dev/null 2>&1; then
        info "Global user extensions disabled: $(gsettings get org.gnome.shell disable-user-extensions 2>/dev/null || echo unknown)"
    else
        info "Global user extensions disabled: unknown (gsettings missing)"
    fi

    info "Extension info:"
    local ext_info enabled shell_state
    if ext_info="$(extension_info)"; then
        printf '%s\n' "$ext_info"
    else
        info "Extension state: not_discovered"
        if [[ -d "$target" ]]; then
            info "Shell discovery: files are installed, but GNOME Shell has not discovered the helper yet."
            print_logout_required "install/update"
        fi
        return
    fi
    enabled="$(extension_info_field "$ext_info" "Enabled")"
    shell_state="$(extension_info_field "$ext_info" "State")"

    if global_user_extensions_disabled; then
        info "Helper state: globally_disabled"
        print_global_disabled_remediation
        return
    fi
    if [[ "$(lower "$enabled")" != "yes" ]]; then
        info "Helper state: disabled"
        info "Run to enable:"
        info "  $SCRIPT_PATH enable"
        return
    fi
    if [[ "$(lower "$shell_state")" != "active" ]]; then
        info "Helper state: inactive_or_error"
        print_logout_required "enable"
        return
    fi

    if command -v gdbus >/dev/null 2>&1 && session_bus_available; then
        info "DBus health:"
        if gdbus call --session \
            --dest "$HELPER_DBUS_SERVICE" \
            --object-path "$HELPER_DBUS_OBJECT_PATH" \
            --method "${HELPER_DBUS_INTERFACE}.${HELPER_DBUS_HEALTH_METHOD}"; then
            :
        else
            info "DBus health: unavailable"
        fi
    else
        info "DBus health: unavailable (gdbus or session bus missing)"
    fi
}

run_install_or_update() {
    local action="$1"
    check_session_for_mutation
    check_install_prerequisites
    local target
    target="$(install_dir)"
    if ! prompt_yes_no_default_no "${action^} and enable GNOME Shell helper at '$target'?"; then
        info "GNOME helper ${action} declined."
        return
    fi
    copy_source_to_install_dir
    info "GNOME helper files copied to $target"

    if global_user_extensions_disabled; then
        print_global_disabled_remediation
        print_logout_required "$action"
        return
    fi

    if [[ "$NO_ENABLE" == true ]]; then
        info "Skipping enable because --no-enable was supplied."
        print_logout_required "$action"
        return
    fi

    if enable_extension; then
        info "GNOME helper enable requested."
    else
        warn "gnome-extensions enable failed; run status for details"
    fi
    print_logout_required "$action"
}

run_enable() {
    check_session_for_mutation
    check_common_prerequisites
    local target ext_info
    target="$(install_dir)"
    if ! ext_info="$(extension_info)"; then
        info "Extension state: not_discovered"
        if [[ -d "$target" ]]; then
            info "Shell discovery: files are installed, but GNOME Shell has not discovered the helper yet."
            print_logout_required "install/update"
            return
        fi
        die "helper files are not installed at $target"
    fi
    printf '%s\n' "$ext_info"
    if global_user_extensions_disabled; then
        print_global_disabled_remediation
        return
    fi
    if ! prompt_yes_no_default_no "Enable GNOME Shell helper '$HELPER_UUID'?"; then
        info "GNOME helper enable declined."
        return
    fi
    if enable_extension; then
        info "GNOME helper enable requested."
    else
        warn "gnome-extensions enable failed; run status for details"
    fi
    print_enable_followup
}

run_disable() {
    check_common_prerequisites
    if ! prompt_yes_no_default_no "Disable GNOME Shell helper '$HELPER_UUID'?"; then
        info "GNOME helper disable declined."
        return
    fi
    disable_extension
    info "GNOME helper disable requested."
    print_logout_required "disable"
}

run_uninstall() {
    local target
    target="$(install_dir)"
    if ! prompt_yes_no_default_no "Disable and remove GNOME Shell helper directory '$target'?"; then
        info "GNOME helper uninstall declined."
        return
    fi
    if command -v gnome-extensions >/dev/null 2>&1; then
        disable_extension
        info "GNOME helper disable requested."
    else
        warn "gnome-extensions missing; removing files only"
    fi
    if [[ -d "$target" ]]; then
        safe_remove_install_dir
        info "GNOME helper files removed from $target"
    else
        info "GNOME helper files were not installed at $target"
    fi
    print_logout_required "uninstall"
}

run_reload() {
    check_session_for_mutation
    check_install_prerequisites
    local target
    target="$(install_dir)"
    if ! prompt_yes_no_default_no "Reload GNOME Shell helper by disabling, removing, reinstalling, enabling, and reporting status at '$target'?"; then
        info "GNOME helper reload declined."
        return
    fi

    disable_extension
    info "GNOME helper disable requested."
    if [[ -d "$target" ]]; then
        safe_remove_install_dir
        info "GNOME helper files removed from $target"
    else
        info "GNOME helper files were not installed at $target"
    fi

    copy_source_to_install_dir
    info "GNOME helper files copied to $target"

    if global_user_extensions_disabled; then
        print_global_disabled_remediation
        print_logout_required "reload"
        run_status
        return
    fi

    if enable_extension; then
        info "GNOME helper enable requested."
    else
        warn "gnome-extensions enable failed; run status for details"
    fi
    print_logout_required "reload"
    run_status
}

main() {
    parse_args "$@"
    case "$ACTION" in
        install|update)
            run_install_or_update "$ACTION"
            ;;
        reload)
            run_reload
            ;;
        enable)
            run_enable
            ;;
        disable)
            run_disable
            ;;
        uninstall)
            run_uninstall
            ;;
        status)
            run_status
            ;;
        *)
            die "unknown action: $ACTION"
            ;;
    esac
}

main "$@"
