# ADR-0029: the camera was aimed at sea level

## Status

Accepted.

## Context

The 3D scene was blank. Not slow, not wrong — blank, on every mode
standing on fetched ground. The panel beside it worked perfectly: forty
nine anchors, a reach of 3,82 km, the terrain described. The picture
showed nothing at all.

Every gesture worked. Dragging turned the camera, the wheel zoomed, the
keys walked, and each one changed the pixels — because a blank screen
lit differently is still a change. Testing that the camera *moved* is not
testing that it is *pointed at anything*, and the difference is the whole
bug.

The framing set `orbit.target = [corridor / 2, width / 2, 0]`.

Relief is drawn five times over, so it reads as relief rather than as a
faint ripple. Ankara's ground is 700 to 1900 m above sea level. Kızılay
sits at about 1150 m, which in view space is 5750 units — and the camera
was aimed at zero from 6000 units away, looking at a point almost the
entire view distance below everything there is.

Modelled terrain averages zero. It hid this completely until the
scenarios moved onto real Ankara (ADR-0021), and then every default view
of every row was empty.

## Decision

Frame on the scene, not on the origin: the middle of the anchors in x and
y, and their mean ground height times the vertical exaggeration in z.
`frameEverything` does it, the first framing calls it, and `F` calls it
again.

## Consequences

It draws.

The lesson is about what the tests were checking. There was a test that
the camera is framed once and not on every refresh, a test that zoom
follows the wheel, a test that dragging follows the ground — all passing,
all about mechanism, none about whether the result was visible. A
screenshot would have caught this on the first run and no amount of
reading would have.

So the framing now has a test that names the two things it must account
for — the ground height and the exaggeration it is drawn with — and the
habit that found it is the one worth keeping: open the page and look at
it.
