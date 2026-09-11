# ADR-0031: the ground you are looking at

## Status

Accepted.

## Context

Zooming in on a mast showed a flat green wall.

The mesh is a few thousand samples spread over the whole site. Over the
rural row that is one every seven hundred metres, so a camera six
kilometres from a hillside sees two facets of it. The elevation model
underneath is thirty metre Copernicus data: the shape of that hill is
measured, and the viewer simply never asked for it.

That made zooming pointless, which is half of what "moving around"
means. The wheel worked perfectly and there was nothing at the end of it.

## Decision

`GET /api/ground?west=&east=&south=&north=` returns a mesh over one
window of the site, at the same budget as the whole. The page asks for
one when the camera has come in far enough that the window is well
inside the site, and drops it when it pulls back out — a finer patch left
in the middle of a coarser mesh is worse than either.

Asked on a timer that every redraw resets, so a drag asks once when it
stops rather than sixty times while it runs, and skipped when the window
rounds to the one already in hand.

## Consequences

The wheel now leads somewhere. At six kilometres the rural hill is
sampled every sixty metres instead of every seven hundred, which is
about as fine as the source data goes.

Nothing is invented. The finer mesh is the same `height_at` the
simulation calls, over the same terrain object, so the ground on screen
and the ground a packet crosses stay the same ground (ADR-0001). It is a
question of which samples get drawn, not of which ground exists.

The cost is one request per settled camera move, answered in about the
time the scene endpoint takes. That is affordable because it is local,
and it would not be over a network — which is the reason this project
does not have to care.
