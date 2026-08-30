# Context

## Requirements

Add `overlay_client/fonts/preferred_fonts.txt` and `overlay_client/fonts/emoji_fallbacks.txt` to the release-exclusion manifest so a release bundle does not replace a user's font preferences during an upgrade.

## Existing pattern

`scripts/release_excludes.json` groups root-level mutable files in `files`. The manifest is validated by `tests/test_release_excludes_manifest.py`. The requested path is nested, so it belongs in `substrings`, which already contains the nested virtual-environment path.

## Scope

Only the release manifest and its focused unit test will change. Installer behaviour is unchanged.
