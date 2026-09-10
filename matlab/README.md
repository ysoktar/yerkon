# MATLAB measurements

Two of the figures in `src/yerkon/defaults.toml` can be measured rather
than guessed. One of them is here.

## Running it

Open MATLAB, `cd` to this folder, and:

```matlab
yerkon_clock_residual
```

It writes `out/clock_residual.csv`. Bring that back and:

```powershell
yerkon calibrate matlab\out\clock_residual.csv
```

which prints the `defaults.toml` entry to paste over the figure it
replaces, with the factor it moves by.

Base MATLAB only. No toolboxes, and nothing to install.

## What `yerkon_clock_residual.m` measures

`clock.crystal.residual_ppm`, currently 0,5 and the least supported
number in the model. It decides whether single-sided two-way ranging
works on the SX1280 at all: in that scheme the residual clock offset
multiplies a sixteen-millisecond reply delay, so 0,5 ppm is 1,20 m and
ten parts per million, uncorrected, is 24,1 m.

The method is the one a real receiver uses. Dechirping an up-chirp gives
a beat at `offset − mu*tau`; dechirping a down-chirp gives
`offset + mu*tau`. Their **sum** is twice the frequency offset with the
timing cancelled. Spectra are accumulated across the preamble before the
peak is taken, because bin estimates are circular and averaging them
arithmetically is wrong, and a parabolic interpolation then gets below
the 1587 Hz bin — which is 0,65 ppm on its own and would otherwise swamp
the answer.

It sweeps signal-to-noise ratio from +5 to +40 dB **after correlation**,
because that is where the link budget lives: a link at the SX1280's
−20 dB in-band threshold sits at +10 dB after the 30,1 dB despreading
gain (ADR-0017).

What it leaves out: phase noise, multipath, and drift during the
exchange. Read the answer as a floor, not as the figure.

## What is not here, and why

The other figure is `radio.sx1280.implementation_floor_m`, the 2,94 m
Stuart Robinson measured on the part. It cannot be measured by simulating
the waveform.

One chip at 1625 kHz is 615 ns, which is 184 m of flight. Interpolating a
correlation peak gets to perhaps a tenth of that, so a chirp simulation
says the part ranges to about 18 m. The part measurably ranges to 2,94 m.
Its timing therefore does not come from the symbol correlation at all: it
comes from a mechanism inside the SX1280 running far finer than a chip,
which Semtech does not document.

A script producing 18 m would contradict a measurement for a reason
already understood, which is worse than no script. That figure needs the
part on a bench, not a simulation.
