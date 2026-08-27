# Rough Idea

Integrate the completed circle and shape-stroke-thickness work from
`feature/circle-shape-pyqt-rendering` into the active
`backend-refactor-implementation` branch without regressing backend-refactor
behavior.

The integration must keep the backend branch's `overlay_groupings.json` because
that file is managed by other plugins and is not part of the circle feature's
contract.
