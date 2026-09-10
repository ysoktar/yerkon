"""What a person sets, and what follows from it.

A Design is the settings someone chooses. An Outcome is everything those
settings imply, computed by the same functions the simulation uses rather
than by a separate table of rules. Keeping the two apart is what lets the
confirmation panel show a person the consequences of an edit before it
happens (ADR-0009), and what keeps range an outcome rather than an input
(ADR-0002).

Nothing here decides anything on its own. It reads the link budget and
reports what it says.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from yerkon.hardware import Antenna, DWM3000, E28_2G4M27S, Radio, SX1280, W24P_U
from yerkon.regulatory import REGIONS, SpectrumRule, TURKEY
from yerkon.rf import (
    Obstruction,
    Terminal,
    closure_range_m,
    evaluate_link,
    usable_range_m,
)
from yerkon.world import (
    BILLBOARD,
    LIGHTING_COLUMN,
    MountingOption,
    ROADSIDE_SIGN,
    SIGN_GANTRY,
    TALL_MAST,
)


@dataclass(frozen=True)
class Design:
    """The settings. Every field here is something a person chooses."""

    #: Whose rules the transmitter obeys. Moves legal power by tens of
    #: decibels and range by more than a factor of two.
    region: SpectrumRule = TURKEY
    #: The module in the anchor. The report names three.
    anchor_radio: Radio = SX1280
    #: The stock antenna from the report's bill of materials.
    antenna: Antenna = W24P_U
    #: What the anchor is mounted on. Sets its height, which is the
    #: single largest lever on range.
    mounting: MountingOption = TALL_MAST
    #: Where the receiver sits: a vehicle roof, or a person's hand.
    receiver_height_m: float = 1.5
    #: Root-mean-square height deviation of the reflecting ground.
    #: Smooth ground reflects and cancels; rough ground scatters.
    surface_roughness_m: float = 0.0
    #: The ranging error a link is allowed before it stops counting as
    #: usable. This is a tolerance, not a prediction.
    target_ranging_sigma_m: float = 5.0

    def __post_init__(self) -> None:
        if self.receiver_height_m <= 0.0:
            raise ValueError("a receiver stands above the ground")
        if self.surface_roughness_m < 0.0:
            raise ValueError("roughness is a magnitude")
        if self.target_ranging_sigma_m <= 0.0:
            raise ValueError("a tolerance of zero cannot be met by any radio")

    @property
    def anchor_height_m(self) -> float:
        return float(self.mounting.height_m.value)

    def with_(self, **edits) -> "Design":
        """A copy with some settings changed. Never mutates."""
        unknown = set(edits) - {f for f in Design.__dataclass_fields__}
        if unknown:
            raise ValueError(
                "not a setting: {}".format(", ".join(sorted(unknown)))
            )
        return replace(self, **edits)


@dataclass(frozen=True)
class Outcome:
    """What the settings imply. Nobody sets these."""

    #: Highest radiated power the region allows this radio and antenna.
    eirp_dbm: float
    #: Anchor height above ground, from the mounting structure.
    anchor_height_m: float
    #: Distance at which ranging error reaches the tolerance. This is
    #: the number siting needs.
    usable_range_m: float
    #: Distance at which the link stops demodulating. Always further,
    #: usually much further, and never the coverage figure. Shown beside
    #: the usable range so the difference cannot be quietly dropped
    #: (ADR-0007).
    closure_range_m: float


def derive(design: Design) -> Outcome:
    """Everything that follows from a Design.

    Deterministic and cheap: a handful of link budgets and one bisection.
    The confirmation panel calls this twice, once for the current design
    and once for the proposed one, and shows the difference.
    """
    obstruction = Obstruction(surface_roughness_m=design.surface_roughness_m)

    anchor = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, design.anchor_height_m)
    )
    receiver = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, design.receiver_height_m)
    )

    reach_m = usable_range_m(
        anchor,
        receiver,
        design.anchor_radio,
        target_sigma_m=design.target_ranging_sigma_m,
        obstruction=obstruction,
        region=design.region,
    )

    # Legal power is read at the usable range, not close in. Antenna
    # gain falls away from the horizon, so a receiver ten metres from a
    # twenty-five metre mast sits far off boresight and its budget shows
    # an EIRP several decibels below what the region actually allows the
    # link that matters.
    at_range = Terminal(
        design.anchor_radio,
        design.antenna,
        (max(reach_m, 10.0), 0.0, design.receiver_height_m),
    )
    budget = evaluate_link(
        anchor, at_range, obstruction=obstruction, region=design.region
    )

    return Outcome(
        eirp_dbm=budget.eirp_dbm,
        anchor_height_m=design.anchor_height_m,
        usable_range_m=reach_m,
        closure_range_m=closure_range_m(
            anchor, receiver, obstruction=obstruction, region=design.region
        ),
    )


# --- What a person can choose from ----------------------------------------
#
# Named so a setting can be typed, written to a file, or put in a dropdown
# without any front end knowing what a SpectrumRule is. The keys are the
# vocabulary; the values are the objects the model runs on.

#: Jurisdictions, keyed as the regulatory module keys them.
REGION_CHOICES = dict(REGIONS)

#: The three anchor modules the report's bill of materials names.
RADIO_CHOICES = {
    "sx1280": SX1280,
    "e28": E28_2G4M27S,
    "dwm3000": DWM3000,
}

#: Where an anchor can go. The first four already stand beside roads; the
#: last has to be built, which is why it costs more and reaches further.
MOUNTING_CHOICES = {
    "sign": ROADSIDE_SIGN,
    "gantry": SIGN_GANTRY,
    "billboard": BILLBOARD,
    "column": LIGHTING_COLUMN,
    "mast": TALL_MAST,
}

#: The stock antenna. One entry today, and a dictionary anyway, because
#: the alternative is a front end that special-cases the only choice.
ANTENNA_CHOICES = {"w24p-u": W24P_U}


def chosen(catalogue: dict, key: str, what: str):
    """Look a name up, and say what the alternatives are when it is wrong.

    A bare KeyError from a typed setting tells a person nothing they can
    act on.
    """
    wanted = key.strip().lower()
    for name, value in catalogue.items():
        if name.lower() == wanted:
            return value
    raise ValueError(
        "no {} called {!r}. Choose one of: {}".format(
            what, key, ", ".join(sorted(catalogue))
        )
    )
