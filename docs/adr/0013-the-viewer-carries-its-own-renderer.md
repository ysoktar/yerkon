# 0013. The viewer draws its own three dimensions

## Status
Accepted.

## Context
The viewer is a local web page. The obvious way to draw a heightfield,
some masts and a grid of coverage cells in three dimensions is a WebGL
library from a content delivery network, and that was the first attempt.

It did not load. The network this project is developed on refuses the
content delivery networks, and so, in general, will a machine on a site
visit, a machine behind a corporate proxy, and a machine with no
connection at all. A viewer that shows an empty grey rectangle when the
network is unavailable is not a viewer.

ADR-0008 already says the project fetches once and runs offline. A page
that reaches out to a third party every time it opens contradicts that
for no gain the study needs.

## Decision
The viewer projects and paints the scene itself, on a plain canvas, in
about two hundred lines. Perspective projection, painter's algorithm,
flat shading from the surface normal, and ray-to-plane intersection for
dragging an anchor. No dependency, nothing to install, and identical
behaviour on every machine.

Masts are drawn at a legible length on screen rather than to scale. A
twenty-five metre mast beside a twenty-four kilometre corridor projects
to less than a pixel, and painting it truthfully would make the control
that matters most impossible to see or to grab. Its height is reported as
a number in the panel, where it can be read instead of guessed at.

## Consequences
The scene is simpler than a WebGL one: no shadows, no smooth normals,
no textures. It shows what the study needs to show, which is where the
ground rises, where the anchors are, how far each one ranges, and which
ground has enough of them for a position.

Painting is done on interaction rather than on every frame, so a few
thousand surfaces cost nothing.

If the scene ever grows past what a canvas can paint at an interactive
rate, the fix is a vendored library file inside the package rather than a
link to somebody's network.
