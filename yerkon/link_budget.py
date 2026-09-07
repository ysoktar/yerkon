"""How far each radio actually reaches, and where that figure comes from.

Link range is the parameter the whole study turns on. It sets how many
anchors a receiver can talk to, which sets the geometry, which sets the
vertical error. An invented range number quietly invents the result, so
each one here starts from a published figure for the exact part the YERKON
report specifies, and the step from that figure to the modelled range is
written down rather than absorbed into a constant.

The published figures are manufacturer reference distances. They are
measured in a clear open field, with 5 dBi antennas at 2.5 m, at the
lowest air rate the part supports. A deployment matches none of those
three conditions, so every modelled range is a stated fraction of the
reference distance and the reason for the fraction is recorded with it.

Sources:
  SX1280 / SX1281 at 12.5 dBm  EBYTE E28-2G4M12S, 3.0 km reference distance
  E28-2G4M27S at 27 dBm        EBYTE E28-2G4M27S(X), 8.0 km reference distance
  DWM3000                      Qorvo publishes no maximum range; see below
"""
from __future__ import annotations

from dataclasses import dataclass

from yerkon.evidence import EvidenceRecord, EvidenceType

REFERENCE_CONDITIONS = (
    "Manufacturer reference distance, measured in a clear open field with "
    "5 dBi antennas at 2.5 m height at the lowest air rate (1 kbps). A "
    "deployment matches none of these: ranging runs at a much higher "
    "bandwidth than 1 kbps, and neither an urban canyon nor a highway "
    "verge is a clear open field."
)

#: Published reference distances, in metres, for the parts the report names.
SX1280_REFERENCE_DISTANCE_M = 3000.0
E28_2G4M27S_REFERENCE_DISTANCE_M = 8000.0


@dataclass(frozen=True)
class LinkRange:
    """A modelled link range and the published figure it was derived from."""

    label: str
    range_m: float
    reference_distance_m: float | None
    evidence: EvidenceRecord

    @property
    def fraction_of_reference(self) -> float | None:
        if not self.reference_distance_m:
            return None
        return self.range_m / self.reference_distance_m


URBAN_LINK_RANGE = LinkRange(
    label="SX1280 at 12.5 dBm, urban canyon",
    range_m=400.0,
    reference_distance_m=SX1280_REFERENCE_DISTANCE_M,
    evidence=EvidenceRecord(
        evidence_type=EvidenceType.ENGINEERING_ASSUMPTION,
        source_name="13% of the 3.0 km SX1280/SX1281 reference distance",
        source_url="https://www.lcsc.com/product-detail/C411312.html",
        source_scope=(
            "Derived from EBYTE's published 3.0 km reference distance for "
            "the 12.5 dBm SX1281 module, the power class the report's urban "
            "broadcast unit uses. " + REFERENCE_CONDITIONS
        ),
        caveats=(
            "The 13% derating for an urban canyon is this project's "
            "judgement, not a measurement. Buildings at 2.4 GHz are the "
            "dominant loss, and the figure is the least defensible number "
            "in the urban scenario. A shorter real range would need a "
            "denser and more expensive grid to hold the same geometry."
        ),
    ),
)

RURAL_LINK_RANGE = LinkRange(
    label="E28-2G4M27S at 27 dBm, open rural line of sight",
    range_m=3000.0,
    reference_distance_m=E28_2G4M27S_REFERENCE_DISTANCE_M,
    evidence=EvidenceRecord(
        evidence_type=EvidenceType.ENGINEERING_ASSUMPTION,
        source_name="37.5% of the 8.0 km E28-2G4M27S reference distance",
        source_url="https://www.lcsc.com/product-detail/C411312.html",
        source_scope=(
            "Derived from EBYTE's published 8.0 km reference distance for "
            "the E28-2G4M27S, the amplified module the report names for "
            "rural units. " + REFERENCE_CONDITIONS
        ),
        caveats=(
            "Derated mainly for ranging bandwidth: the 8 km figure is a "
            "1 kbps communication result, and SX1280 ranging runs far wider. "
            "Mounting is higher than the 2.5 m test condition, which works "
            "the other way. Stuart Robinson's published SX1280 ranging at "
            "40 km and 85 km was air-to-ground with clear Fresnel clearance "
            "and does not transfer to a roadside link."
        ),
    ),
)

TUNNEL_LINK_RANGE = LinkRange(
    label="DWM3000 UWB inside a tunnel bore",
    range_m=150.0,
    reference_distance_m=None,
    evidence=EvidenceRecord(
        evidence_type=EvidenceType.ENGINEERING_ASSUMPTION,
        source_name="Practical DWM3000 range reports, upper half of the band",
        source_url="https://www.qorvo.com/products/p/DWM3000",
        source_scope=(
            "Qorvo publishes no maximum range for the DWM3000. Reported "
            "practical figures span roughly 50-100 m for commercial modules "
            "in ordinary use, against 300 m advertised for the DWM1000 "
            "predecessor and 500 m demonstrated on DW3000 boards with "
            "external antennas in clear line of sight."
        ),
        caveats=(
            "150 m sits in the upper half of the practical band, on the "
            "argument that a tunnel bore guides the signal instead of "
            "letting it spread spherically. This is the single most "
            "consequential assumption in the study: it decides whether the "
            "report's own 150 m node spacing can produce a fix at all."
        ),
    ),
)


def minimum_spacing_for_fix(
    link_range_m: float, minimum_anchors: int = 4, sides: int = 1
) -> float:
    """Largest node spacing along a corridor that still yields a 3D fix.

    A receiver on a line of anchors spaced ``S`` apart with link range ``R``
    hears about ``2R/S`` of them per line of anchors. Solving for the
    minimum anchor count gives the spacing below.

    This is what rules out the report's own tunnel figure. At the DWM3000's
    real range, 150 m spacing leaves a receiver hearing one or two nodes,
    and a 3D fix needs four.
    """
    if link_range_m <= 0:
        raise ValueError("link_range_m must be positive")
    if minimum_anchors < 4:
        raise ValueError("a 3D fix from absolute ranges needs at least 4 anchors")
    if sides < 1:
        raise ValueError("sides must be at least 1")
    return 2.0 * link_range_m * sides / minimum_anchors
