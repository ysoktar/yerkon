# ADR-0030: one depth per thing is not enough

## Status

Accepted.

## Context

The scene is painted back to front: every surface is projected, sorted by
how far away it is, and drawn in that order. That is the whole renderer,
and it is why the viewer needs no library and works offline (ADR-0008).

It has one assumption, and the assumption is that a thing is at *a*
distance. Opening the rural row showed what happens when it is not.

The road was a twenty kilometre circuit sampled at a hundred and sixty
points and handed over as one item, with the average depth of those
points. Every hill nearer to the camera than that average was painted
over the whole of it — including the near legs, which are in front of the
hill. Half the circuit disappeared, and the half that survived made an
area deployment look like a straight line drawn across a field. Nothing
on screen said which was real.

Splitting it into one item per segment fixed that and exposed the same
assumption a level down. A ground quad is seven hundred metres across on
this site, and it too sorts at the depth of its middle: seen at a grazing
angle its middle is most of a cell nearer than its far edge, so the quad
covered the half of the road lying on its far side. The road came back as
a dashed line.

Two more things came from the same reading of the frame:

The mesh was a fixed hundred by forty whatever the site. Twenty
kilometres by twenty was therefore sampled every 460 m along and every
1100 m across — the ground came out in stripes and a hill read as a
ridge, because the mesh could only resolve it in one direction.

And adjacent quads are antialiased independently, so the background
showed through every shared edge as a hairline. Four thousand of them
read as a wire grid laid over the hill rather than as ground.

Two smaller things came out of the same place. A corner behind the eye
cannot be projected, and the whole surface was being dropped for it — so
the ground directly under a close camera went missing at exactly the
distance where it is the only thing on screen. And the coverage overlay
was held sixty units clear of the mesh to stop the painter burying it,
which is twelve metres of real ground drawn five times over: close up it
hovers visibly above the hill it describes.

## Decision

A line that lies on the ground is pulled towards the camera by one mesh
cell before it is sorted. That is the scale at which a quad's single
depth stops describing the whole of it, so it is the right bias: enough
to win against the quad it lies on, not enough to win against a hill in
front of it. The page knows the mesh, so the page supplies it.

The mesh is sampled from the site's own proportions, for cells that are
roughly square at a fixed budget of about four thousand quads.

Each quad is grown half a pixel from its own middle, which closes the
join with its neighbour. Stroking every quad in its own colour closes it
too and costs a second pass over all four thousand.

A shape with a corner behind the eye is cut at the near plane and the
part in front is drawn.

The coverage overlay sits on the ground and is biased forward like
anything else drawn on it — by its own half-width as well as the mesh
cell, because both surfaces are wide and both sort at the depth of their
middles, so the two spreads add.

## Consequences

The road is a road. The ground is ground.

What generalises: a painter's renderer is exact only for things small
against the depth differences between them, and both failures here were
the same mistake at different scales. Anything drawn on a surface rather
than at a point needs either a bias or a finer subdivision, and the size
of the surface is what says how much.

What does not generalise, and is worth saying plainly: this is a depth
bias, which is a fudge. It is correct for lines lying on the terrain and
it would not be correct for a wall standing on it. If the scene ever
grows something with real vertical extent, the answer is per-pixel depth,
which means WebGL, which means the trade in ADR-0008 gets made again.
