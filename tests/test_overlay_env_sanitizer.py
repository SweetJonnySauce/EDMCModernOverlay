from overlay_plugin import overlay_env_sanitizer


def test_sanitize_removes_risky_keys_and_ld_library_path_without_mel() -> None:
    source_env = {
        "LD_PRELOAD": "/steam/overlay.so",
        "QT_PLUGIN_PATH": "/steam/qt/plugins",
        "QT_QPA_PLATFORM_PLUGIN_PATH": "/steam/qt/platforms",
        "LD_LIBRARY_PATH": "/steam/lib",
        "KEEP_ME": "ok",
    }

    sanitized, result = overlay_env_sanitizer.sanitize_overlay_environment(source_env)

    assert sanitized["KEEP_ME"] == "ok"
    assert "LD_PRELOAD" not in sanitized
    assert "QT_PLUGIN_PATH" not in sanitized
    assert "QT_QPA_PLATFORM_PLUGIN_PATH" not in sanitized
    assert "LD_LIBRARY_PATH" not in sanitized
    assert result.skipped_opt_out is False
    assert result.actions == {
        "LD_PRELOAD": "removed",
        "QT_PLUGIN_PATH": "removed",
        "QT_QPA_PLATFORM_PLUGIN_PATH": "removed",
        "LD_LIBRARY_PATH": "removed",
    }


def test_sanitize_uses_mel_library_path_when_present() -> None:
    source_env = {
        "LD_LIBRARY_PATH": "/steam/lib",
        "MEL_LD_LIBRARY_PATH": "/host/lib",
    }

    sanitized, result = overlay_env_sanitizer.sanitize_overlay_environment(source_env)

    assert sanitized["LD_LIBRARY_PATH"] == "/host/lib"
    assert result.actions == {"LD_LIBRARY_PATH": "set-from-mel"}


def test_sanitize_opt_out_preserves_linker_keys() -> None:
    source_env = {
        "EDMC_OVERLAY_PRESERVE_LD_ENV": "1",
        "LD_PRELOAD": "/steam/overlay.so",
        "QT_PLUGIN_PATH": "/steam/qt/plugins",
        "QT_QPA_PLATFORM_PLUGIN_PATH": "/steam/qt/platforms",
        "LD_LIBRARY_PATH": "/steam/lib",
    }

    sanitized, result = overlay_env_sanitizer.sanitize_overlay_environment(source_env)

    assert sanitized == source_env
    assert result.skipped_opt_out is True
    assert result.actions == {
        "LD_PRELOAD": "preserved-by-optout",
        "QT_PLUGIN_PATH": "preserved-by-optout",
        "QT_QPA_PLATFORM_PLUGIN_PATH": "preserved-by-optout",
        "LD_LIBRARY_PATH": "preserved-by-optout",
    }
