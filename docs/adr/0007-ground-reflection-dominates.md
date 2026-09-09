# 0007. Ground reflection, and the difference between reaching and ranging

## Status
Accepted. Corrects this repository's own first version of `rf.py`.

## Context
The first link budget used free-space loss plus knife-edge diffraction.
Over flat ground it therefore reported no loss beyond free space, and
concluded that the stock hardware reaches 10 km with over 50 dB to spare.

That is wrong for every geometry in this project. A radio a few metres
above the ground has a second path: the ray that bounces off the surface.
Past the breakpoint distance, `4 * h1 * h2 / wavelength`, the two arrive in
opposition and loss grows with the fourth power of distance rather than the
second.

Measured against the previous model at 10 km:

| Mount | Breakpoint | Understated by |
|---|---|---|
| Road sign, 3 m | 196 m | 34,1 dB |
| Sign gantry, 6 m | 392 m | 28,1 dB |
| Billboard, 10 m | 654 m | 23,7 dB |
| Tall mast, 25 m | 1634 m | 15,7 dB |
| Tower, 35 m | 2288 m | 12,8 dB |

## Decision
Path loss is the two-ray dual-slope model, plus diffraction where terrain
rises into the path, plus clutter. The two are separate effects: reflection
acts over perfectly flat ground, diffraction needs an obstacle.

The budget also now reports **usable range** separately from whether the
link closes, and siting uses the former.

## Consequences
The headline claim changes. The links still close, because a spread
waveform keeps demodulating 30 dB below the noise floor. What collapses is
timing precision, which follows the signal-to-noise ratio.

Usable range, at the distance where ranging error stays under a target:

| Mount | sigma 3 m | sigma 5 m | sigma 10 m |
|---|---|---|---|
| Road sign, 3 m | 1,5 km | 1,9 km | 2,6 km |
| Sign gantry, 6 m | 2,3 km | 2,9 km | 3,9 km |
| Billboard, 10 m | 3,1 km | 4,0 km | 5,3 km |
| Lighting column, 12 m | 3,4 km | 4,4 km | 6,0 km |
| Tall mast, 25 m | 4,9 km | 6,4 km | 9,0 km |
| Tower, 35 m | 5,8 km | 7,5 km | 10,7 km |

So the 5 to 10 km requirement is met only by tall structures, and only if
several metres of ranging error is acceptable at the far end. A 25 m mast
ranges to 5 m at 6,4 km. Nothing mounted on existing roadside furniture
reaches 5 km at any useful precision.

Reporting the closure distance as the range would have overstated anchor
coverage by a factor of two to five, and the service area, which is the
denominator of every cost figure in the table, by its square.
