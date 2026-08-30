# Requirements decisions

## Question

Which payloads should change stroke semantics?

## Answer

Only `shape="circle"`. The request is to make circle `thickness=1` visually
match the legacy vector line on the left of the supplied comparison image.
Rectangles keep their existing logical-width, viewport-scaled behavior.

## Question

What does a circle thickness value mean after the change?

## Answer

It is an integer logical Qt pixel width, clamped to at least one pixel. It is
not multiplied by Fit/Fill viewport scale. Qt continues to handle the display
device-pixel ratio consistently with the legacy vector line.
