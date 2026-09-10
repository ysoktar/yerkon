"""Two-way ranging: the exchange, its clocks, and what it costs in time.

A range is not read off a link budget. Two radios trade timestamped
frames, and the number that comes back carries three errors that have
nothing to do with signal strength:

The **reply delay** is long. A frame at SF10 takes fifteen milliseconds,
and both clocks run at their own rate throughout it. In single-sided
ranging that offset lands on the answer undivided.

The **exchange takes time**, so a receiver cannot range against every
anchor at once. The ranges in one round are measured seconds apart at
worst and milliseconds apart at best, and a vehicle moves between them.

The **schedule is shared**. Anchors that are ranging one receiver are not
ranging another.

Everything here produces RangeObservations and nothing else. See ADR-0003.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import numpy as np

from yerkon.evidence import Sourced
from yerkon.hardware import SPEED_OF_LIGHT_M_S, Radio
from yerkon.observation import RangeObservation
from yerkon.regulatory import TURKEY, SpectrumRule
from yerkon.settings import DEFAULTS, Settings
from yerkon.terms import ALL as ALL_TERMS, Terms
from yerkon.rf import (
    Obstruction,
    Terminal,
    cramer_rao_sigma_m,
    evaluate_link,
)


# --- Clocks ---------------------------------------------------------------


@dataclass(frozen=True)
class Clock:
    """A crystal, described by how wrong it is rather than how fast.

    Only two numbers matter to ranging. ``tolerance_ppm`` is how far the
    part can sit from nominal before anybody corrects it: unit to unit,
    over temperature, over life. ``residual_ppm`` is what survives the
    receiver's own frequency-offset estimate, which every coherent
    receiver has to make in order to demodulate at all.

    The gap between the two is large and it decides whether single-sided
    ranging is usable. Uncorrected, ten parts per million across a
    fifteen millisecond reply is seventy-five nanoseconds, which is
    twenty-two metres. Corrected to half a part per million it is one
    metre.
    """

    part: str
    tolerance_ppm: Sourced
    residual_ppm: Sourced

    def __post_init__(self) -> None:
        if float(self.tolerance_ppm.value) < 0.0:
            raise ValueError("a tolerance is a magnitude")
        if float(self.residual_ppm.value) < 0.0:
            raise ValueError("a residual is a magnitude")
        if float(self.residual_ppm.value) > float(self.tolerance_ppm.value):
            raise ValueError(
                "correcting a clock cannot leave it further out than it started"
            )

    def offset_ppm(self, corrected: bool = True) -> float:
        return float(
            (self.residual_ppm if corrected else self.tolerance_ppm).value
        )


def clocks(settings: Settings = DEFAULTS) -> dict:
    """The oscillators, from a settings file.

    Neither module publishes a crystal tolerance and nobody publishes
    what a frequency-offset estimate leaves behind, so both come from the
    settings file. The residual is the least supported number in the
    whole ranging model and it decides whether single-sided ranging works
    at all on the slow radio.
    """
    return {
        "crystal": Clock(
            part="52 MHz crystal, frequency-offset corrected",
            tolerance_ppm=settings.sourced("clock.crystal.tolerance_ppm"),
            residual_ppm=settings.sourced("clock.crystal.residual_ppm"),
        ),
        "tcxo": Clock(
            part="temperature-compensated oscillator",
            tolerance_ppm=settings.sourced("clock.tcxo.tolerance_ppm"),
            residual_ppm=settings.sourced("clock.tcxo.residual_ppm"),
        ),
    }


CLOCKS = clocks()

CRYSTAL = CLOCKS["crystal"]
"""The clock assumed in both modules until a measurement replaces it."""

TCXO = CLOCKS["tcxo"]
"""What an anchor could be fitted with, for asking whether it is worth it."""


# --- The exchange ---------------------------------------------------------


@dataclass(frozen=True)
class Scheme:
    """How many frames a range costs, and what the clocks do to it."""

    name: str
    #: Frames on the air per range.
    messages: int
    #: Whether the arithmetic cancels the clock offset to first order.
    cancels_offset: bool
    note: str = ""

    def clock_error_s(
        self, reply_s: float, time_of_flight_s: float, offset_ppm: float
    ) -> float:
        """Timing error the clocks contribute to one range, in seconds.

        Single-sided ranging subtracts a reply delay measured on the
        far radio's clock from a round trip measured on the near one, so
        the whole offset multiplies the reply delay. That delay is a
        frame long, which is why this term dominates on a slow radio.

        Double-sided ranging trades a second reply so the offsets divide
        out. What is left is second order and multiplies the flight time
        instead, which is thousands of times shorter, so the error grows
        with distance rather than with the frame.
        """
        fraction = offset_ppm * 1e-6
        if self.cancels_offset:
            return fraction * time_of_flight_s
        return 0.5 * fraction * reply_s


SINGLE_SIDED = Scheme(
    name="single-sided two-way ranging",
    messages=2,
    cancels_offset=False,
    note=(
        "Poll and reply. Cheapest in airtime and unusable on a slow radio "
        "without frequency correction, because the reply delay carries the "
        "clock offset straight onto the answer."
    ),
)

DOUBLE_SIDED = Scheme(
    name="double-sided two-way ranging",
    messages=3,
    cancels_offset=True,
    note=(
        "Poll, reply, final. Half again the airtime, and it removes the "
        "reply delay from the error entirely."
    ),
)

SCHEMES = {"single": SINGLE_SIDED, "double": DOUBLE_SIDED}


# --- How long it all takes ------------------------------------------------

#: Bytes in a ranging frame's payload, and the turnaround before a reply.
#:
#: Both come from the settings file, like every other figure nobody
#: supplied. See `yerkon.settings`.
RANGING_PAYLOAD_BYTES = int(DEFAULTS.number("ranging.payload_bytes"))

DEFAULT_TURNAROUND_S = DEFAULTS.number("ranging.turnaround_s")


def frame_duration_s(radio: Radio, payload_bytes: int = RANGING_PAYLOAD_BYTES) -> float:
    """How long one ranging frame occupies the air, in seconds.

    Preamble plus payload, both counted in the radio's own symbols. The
    preamble is the same one the processing gain is taken over, so a
    radio cannot be given cheap airtime and a generous gain at once.
    """
    if payload_bytes < 0:
        raise ValueError("a payload is a count of bytes")
    symbol_s = float(radio.symbol_duration_s.value)
    preamble = float(radio.preamble_symbols.value)
    # Bandwidth-time product of one symbol. For a spread waveform this is
    # exactly the spreading factor. For the impulse radio it is within a
    # couple of bits of the real payload rate, and the preamble is a
    # thousand symbols long, so the payload term barely shows either way.
    bits_per_symbol = max(
        math.log2(float(radio.ranging_bandwidth_hz.value) * symbol_s), 1.0
    )
    payload_symbols = math.ceil(8.0 * payload_bytes / bits_per_symbol)
    return (preamble + payload_symbols) * symbol_s


def reply_delay_s(
    radio: Radio,
    payload_bytes: int = RANGING_PAYLOAD_BYTES,
    turnaround_s: float = DEFAULT_TURNAROUND_S,
) -> float:
    """Time between a poll leaving and its reply leaving, in seconds.

    The far radio has to hear the whole poll before it can answer, so
    this is a frame plus a turnaround. It is the delay the clock offset
    multiplies in single-sided ranging.
    """
    return frame_duration_s(radio, payload_bytes) + turnaround_s


def exchange_duration_s(
    radio: Radio,
    scheme: Scheme = DOUBLE_SIDED,
    payload_bytes: int = RANGING_PAYLOAD_BYTES,
    turnaround_s: float = DEFAULT_TURNAROUND_S,
) -> float:
    """Air time one range costs, start to finish, in seconds."""
    frame_s = frame_duration_s(radio, payload_bytes)
    return scheme.messages * frame_s + (scheme.messages - 1) * turnaround_s


def ranges_per_second(
    radio: Radio,
    scheme: Scheme = DOUBLE_SIDED,
    duty_cycle: float = 1.0,
    payload_bytes: int = RANGING_PAYLOAD_BYTES,
    turnaround_s: float = DEFAULT_TURNAROUND_S,
) -> float:
    """How many ranges the medium supports per second.

    ``duty_cycle`` is the share of the second this link may use. A band
    with a transmit duty limit, or a channel shared between receivers,
    takes its cut here.
    """
    if not 0.0 < duty_cycle <= 1.0:
        raise ValueError("a duty cycle is a fraction of the second")
    return duty_cycle / exchange_duration_s(
        radio, scheme, payload_bytes, turnaround_s
    )


# --- One measurement ------------------------------------------------------


def sigma_terms_m(
    budget,
    radio: Radio,
    clock: Clock = CRYSTAL,
    scheme: Scheme = DOUBLE_SIDED,
    corrected: bool = True,
    turnaround_s: float = DEFAULT_TURNAROUND_S,
) -> dict:
    """One sigma on a single range, split into the three things that make it.

    The waveform bound falls with signal strength and rises with
    distance. The clock term comes from the exchange and mostly does not
    care about distance at all. Those two are independent, so they add in
    quadrature.

    The part's measured floor is not a fourth independent error; it is a
    statement that the model must not predict better than the only
    measurement anybody has taken of the part. It enters here as whatever
    has to be added in quadrature to reach that floor, and it is zero
    wherever the physics already sits above it. Summed, the three
    reproduce `max(hypot(waveform, clock), floor)` exactly, so nothing
    about the total changed when it was split.
    """
    waveform_m = cramer_rao_sigma_m(budget, radio)
    clock_s = scheme.clock_error_s(
        reply_delay_s(radio, turnaround_s=turnaround_s),
        budget.distance_m / SPEED_OF_LIGHT_M_S,
        clock.offset_ppm(corrected),
    )
    clock_m = clock_s * SPEED_OF_LIGHT_M_S
    floor_m = float(radio.implementation_floor_m.value)
    return {
        "waveform": waveform_m,
        "clock": clock_m,
        "floor": math.sqrt(
            max(floor_m * floor_m - waveform_m * waveform_m - clock_m * clock_m, 0.0)
        ),
    }


def _quadrature(terms: dict, live: "Terms" = ALL_TERMS) -> float:
    """The sigma of whichever terms are switched on, in metres."""
    return math.sqrt(
        sum(
            value * value
            for name, value in terms.items()
            if getattr(live, name)
        )
    )


def measurement_sigma_m(
    budget,
    radio: Radio,
    clock: Clock = CRYSTAL,
    scheme: Scheme = DOUBLE_SIDED,
    corrected: bool = True,
    turnaround_s: float = DEFAULT_TURNAROUND_S,
) -> float:
    """One sigma on a single range, in metres. Which term binds says what to fix."""
    return _quadrature(
        sigma_terms_m(budget, radio, clock, scheme, corrected, turnaround_s)
    )


def measure(
    anchor: Terminal,
    receiver: Terminal,
    at_s: float,
    rng: np.random.Generator,
    anchor_id: str = "",
    clock: Clock = CRYSTAL,
    scheme: Scheme = DOUBLE_SIDED,
    corrected: bool = True,
    obstruction: Optional[Obstruction] = None,
    region: SpectrumRule = TURKEY,
    frequency_hz: float = 2450e6,
    survey_error_m: float = 0.0,
    packet_loss: float = 0.0,
    terms: "Terms" = ALL_TERMS,
) -> Optional[RangeObservation]:
    """One exchange. Returns nothing when the link does not close.

    ``rng`` is passed in and never created here. A previous version of
    this project held a module-level generator, so the second scenario in
    a process drew from wherever the first stopped and every swept
    comparison it published was contaminated. Nothing in this module owns
    randomness.

    The observation carries the anchor's surveyed position, which the
    receiver knows, and no part of the receiver's own.
    """
    if not share_a_waveform(anchor.radio, receiver.radio):
        raise ValueError(
            "{} and {} do not share a ranging waveform".format(
                anchor.radio.part, receiver.radio.part
            )
        )

    budget = evaluate_link(
        anchor, receiver, frequency_hz, obstruction=obstruction, region=region
    )
    if not budget.closes:
        return None

    # Everything the link budget does not model: interference from the
    # rest of a shared band, a collision with traffic this study does not
    # simulate, a fade the two-ray average smooths over. An exchange that
    # fails this way produces nothing, exactly like one that never closed.
    if terms.packet_loss and packet_loss > 0.0 and float(rng.random()) < packet_loss:
        return None

    parts = sigma_terms_m(budget, anchor.radio, clock, scheme, corrected)
    sigma_m = _quadrature(parts)
    # What is actually drawn, which is only the terms this run leaves
    # live. The variance reported below stays whole either way: the
    # receiver's own belief about its measurement does not change because
    # an experiment silenced one source, and holding it fixed is what
    # makes two runs comparable. A filter reweighted between them would
    # be measuring its own gains rather than the error under study.
    noise_m = _quadrature(parts, terms)

    # Two errors that are not noise and must not be drawn as noise.
    #
    # The excess path is what the signal actually travelled when
    # something stood in the way, so it is added rather than sampled and
    # it is always positive. The survey error is a property of the
    # anchor, fixed for the life of the installation, and it is passed in
    # already drawn for that reason. Neither averages out over repeated
    # measurements, which is what makes them worse than their size
    # suggests (ADR-0019).
    measured = (
        budget.distance_m
        + (budget.excess_path_m if terms.excess_path else 0.0)
        + (survey_error_m if terms.survey else 0.0)
        + (float(rng.normal(0.0, noise_m)) if noise_m > 0.0 else 0.0)
    )

    return RangeObservation(
        at_s=at_s,
        anchor_position_m=anchor.position_m,
        # A range is a magnitude. A draw large enough to go negative is a
        # useless measurement, not a negative distance.
        measured_range_m=max(measured, 0.0),
        # What the receiver believes about its own measurement, which is
        # the noise it knows about and not the biases it does not. A
        # variance inflated to cover a bias would be a receiver that
        # knows it is being lied to, and it does not.
        variance_m2=sigma_m * sigma_m,
        anchor_id=anchor_id,
    )


def share_a_waveform(one: Radio, other: Radio) -> bool:
    """Whether two radios can range against each other at all.

    The urban and rural anchors are different parts on the same silicon
    and can. An impulse radio and a spread one cannot, and pairing them
    would produce a confident number from an exchange that is not
    physically possible.

    A receiver carrying both modules is not one radio, so a caller asks
    this per module rather than per unit.
    """
    return (
        float(one.ranging_bandwidth_hz.value)
        == float(other.ranging_bandwidth_hz.value)
    )


def audible(anchor: Terminal, radios: Sequence[Radio]) -> Optional[Radio]:
    """Which of a receiver's modules, if any, can hear this anchor."""
    for radio in radios:
        if share_a_waveform(anchor.radio, radio):
            return radio
    return None


# --- A round of them ------------------------------------------------------


def round_robin(
    anchors: Sequence[tuple[str, Terminal]],
    receiver_at: Callable[[float], Terminal],
    start_s: float,
    rng: np.random.Generator,
    radio: Radio,
    clock: Clock = CRYSTAL,
    scheme: Scheme = DOUBLE_SIDED,
    duty_cycle: float = 1.0,
    obstruction_between: Optional[
        Callable[[Terminal, Terminal], Obstruction]
    ] = None,
    region: SpectrumRule = TURKEY,
) -> tuple[RangeObservation, ...]:
    """Range against each anchor in turn, one after another.

    Not simultaneously, which is the point. ``receiver_at`` is asked
    where the receiver is at each exchange's own instant, so a moving
    receiver is in a different place for every range in the round. At a
    hundred kilometres an hour and fifteen milliseconds a frame, that
    spread is metres, which is the same size as the ranging error it sits
    beside.

    Anchors whose link does not close are simply absent from the result;
    they cost their slot either way, because the receiver waited for a
    reply that never came.

    ``obstruction_between`` is asked what the ground does to each pair,
    because it does something different to each. One obstruction shared
    across a round would give the anchor behind a hill the same clearance
    as the one in plain sight.
    """
    slot_s = exchange_duration_s(radio, scheme) / max(duty_cycle, 1e-9)
    observations = []
    for index, (anchor_id, anchor) in enumerate(anchors):
        at_s = start_s + index * slot_s
        receiver = receiver_at(at_s)
        observation = measure(
            anchor,
            receiver,
            at_s,
            rng,
            anchor_id=anchor_id,
            clock=clock,
            scheme=scheme,
            obstruction=(
                None if obstruction_between is None
                else obstruction_between(anchor, receiver)
            ),
            region=region,
        )
        if observation is not None:
            observations.append(observation)
    return tuple(observations)
