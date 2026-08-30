# Plan

## Test strategy

- Input: parsed `scripts/release_excludes.json` manifest.
- Expected output: its `substrings` list contains exactly the requested nested preference-file path.
- Test type: unit test, because this is deterministic JSON-manifest data with no EDMC lifecycle dependency.

## Implementation

1. Extend the existing release-excludes manifest test with the new assertion.
2. Add the nested path to the manifest's `substrings` list.
3. Run the focused pytest test and validate the JSON parses.

## Follow-up: emoji fallback preferences

- Input: parsed manifest.
- Expected output: `substrings` contains `overlay_client/fonts/emoji_fallbacks.txt`.
- Implementation: add the focused assertion, then add the path beside `preferred_fonts.txt` and rerun the same validation.

## Risks

The path must be a `substrings` entry rather than a root-level `files` entry; otherwise the release packaging filter may not match it.
