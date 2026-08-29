# Monitor-to-canonical coordinate utility

## Requirements

- Accept a monitor-space rectangle (`x`, `y`, `w`, `h`) and monitor dimensions.
- Return the matching legacy canvas rectangle in the canonical 1280x960 space.
- Mirror the overlay client's existing uniform `fit` and `fill` viewport mappings.
- Provide a standalone, dependency-free command-line script suitable for copying
  coordinates into payload definitions.

## Existing implementation context

- `overlay_client/viewport_helper.py` defines the canonical canvas as 1280x960
  and computes uniform scale plus `fit` offsets.
- `overlay_client/client_config.py` defaults the client scale mode to `fill`.
- Existing script tests import modules from `scripts` directly and test command
  entry points with pytest.

## Dependency map

`scripts/monitor_to_canonical.py` -> `overlay_client.viewport_helper`

The utility calls the existing viewport transform and algebraically inverts it:
subtract the viewport offset from position, then divide positions and sizes by
the uniform scale. No runtime, UI, socket, or EDMC lifecycle component changes.

## Uncertainty resolved

The original request describes reverse conversion generally. The implementation
will expose `--scale-mode` because `fit` and `fill` are observably different on
non-4:3 monitors. It defaults to `fill`, matching the client configuration.
