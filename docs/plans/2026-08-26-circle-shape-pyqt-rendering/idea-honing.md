# Requirements clarification

## Question 1

What caller-facing capability should the circle API provide?

## Answer 1

The caller should be able to send a circle with a shape token, coordinates, radius, and stroke thickness, for example `send_shape('circle', x=100, y=100, radius=50, thickness=2)`. The API must also accept border color and fill color.

## Question 2

Should circles retain the existing stable payload ID as the first argument?

## Answer 2

Yes. Circles must retain the existing stable payload-ID behavior so callers can update or clear them by ID.

## Question 3

For a circle, should `x` and `y` refer to its center point or its bounding-box top-left corner?

## Answer 3

They refer to the circle center point.

## Question 4

Should the existing TTL rule apply unchanged: a positive value expires after that many seconds, while `ttl <= 0` keeps the circle until replacement or clearing?

## Answer 4

Yes. Circle TTL behavior must match rectangle TTL behavior.

## Question 5

What should happen when `radius <= 0` or `thickness <= 0`?

## Answer 5

Reject/drop the payload and emit a warning. Do not clamp invalid values.

## Requirements-completeness check

The requester confirmed that the requirements are complete and approved proceeding to repository research and detailed planning.
