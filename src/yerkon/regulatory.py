"""What each jurisdiction lets a transmitter radiate.

Region is not a footnote here. The same radio and the same antenna reach
very different distances depending on which rulebook applies, because the
2,4 GHz limits differ by more than twenty decibels between Turkey and the
United States. A study that fixes one region silently answers a narrower
question than it appears to.

Every limit below is a clause in a published rule, cited on the constant.
Where a project assumption is needed it is marked as one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from yerkon.evidence import Provenance, Sourced

ISM_2G4_HZ = (2400e6, 2483.5e6)
"""The licence-exempt band all three anchor radios work in."""


@dataclass(frozen=True)
class SpectrumRule:
    """One jurisdiction's ceiling on radiated power in a band.

    Three ceilings, and the binding one is whichever comes out lowest.

    ``max_eirp_dbm`` caps the radiated total. ``max_eirp_density_dbm_per_mhz``
    caps it per megahertz, so it rises with occupied bandwidth.
    ``max_conducted_dbm`` caps what leaves the transmitter before the
    antenna, which is the form the United States rule takes.

    ``antenna_gain_allowance_dbi`` is how much gain the conducted limit
    already assumes. Gain beyond it must be paid back out of transmit
    power, at ``gain_payback_ratio`` decibels of power per decibel of
    excess gain. A ratio below one is the concession fixed point-to-point
    links get.

    ``idle_after_occupancy`` is how long, as a share of each channel
    occupancy, the equipment must then stay silent. Adaptive equipment
    under EN 300 328 listens before it talks and rests afterwards; the
    rest is time the ranging schedule cannot use.
    """

    region: str
    max_eirp_dbm: Optional[Sourced] = None
    max_eirp_density_dbm_per_mhz: Optional[Sourced] = None
    max_conducted_dbm: Optional[Sourced] = None
    antenna_gain_allowance_dbi: float = 0.0
    gain_payback_ratio: float = 1.0
    idle_after_occupancy: float = 0.0
    note: str = ""

    @property
    def channel_share(self) -> float:
        """Share of the second a transmitter under this rule may occupy."""
        return 1.0 / (1.0 + self.idle_after_occupancy)

    def permitted_eirp_dbm(
        self, bandwidth_hz: float, antenna_gain_dbi: float, radio_max_dbm: float
    ) -> float:
        """Highest legal radiated power for this configuration, in dBm.

        Takes the radio's own maximum too, because a rule that allows more
        than the hardware can produce does not make the hardware louder.
        """
        if bandwidth_hz <= 0.0:
            raise ValueError("bandwidth_hz must be positive")

        ceilings = [radio_max_dbm + antenna_gain_dbi]

        if self.max_eirp_dbm is not None:
            ceilings.append(float(self.max_eirp_dbm.value))

        if self.max_eirp_density_dbm_per_mhz is not None:
            ceilings.append(
                float(self.max_eirp_density_dbm_per_mhz.value)
                + 10.0 * math.log10(bandwidth_hz / 1e6)
            )

        if self.max_conducted_dbm is not None:
            excess = max(antenna_gain_dbi - self.antenna_gain_allowance_dbi, 0.0)
            allowed_conducted = float(self.max_conducted_dbm.value) - (
                excess * self.gain_payback_ratio
            )
            ceilings.append(allowed_conducted + antenna_gain_dbi)

        return min(ceilings)


TURKEY = SpectrumRule(
    region="Türkiye",
    max_eirp_dbm=Sourced(
        20.0, "dBm", Provenance.STANDARD,
        "TS EN 300 328, as adopted by the BTK short-range device regulation",
    ),
    max_eirp_density_dbm_per_mhz=Sourced(
        10.0, "dBm/MHz", Provenance.STANDARD,
        "TS EN 300 328, modulation other than frequency hopping",
    ),
    note=(
        "Turkey follows the CEPT position and cites the harmonised "
        "standard directly, so the limits match the European ones. The "
        "density cap binds at every SX1280 bandwidth, which is why legal "
        "power here rises with bandwidth instead of being flat."
    ),
)

TURKEY_FREQUENCY_HOPPING = SpectrumRule(
    region="Türkiye, uyarlamalı frekans atlamalı (belgelendirilmiş)",
    max_eirp_dbm=Sourced(
        20.0, "dBm", Provenance.STANDARD,
        "TS EN 300 328, as adopted by the BTK short-range device regulation",
    ),
    # Adaptive, because the non-adaptive mode allows 5 ms on a channel
    # and a ranging frame is about 15 ms: after each occupancy at least
    # 5 % of it idle (EN 300 328 V2.2.2, 4.3.1.7.2.2; ADR-0092).
    idle_after_occupancy=0.05,
    note=(
        "The same standard for equipment certified as frequency hopping: "
        "the density limit applies to other modulations only, so 20 dBm "
        "e.i.r.p. is the whole ceiling. SX1280 ranging already hops its "
        "channels; the equipment has to be tested as FHSS by an accredited "
        "laboratory, and EN 300 328 then sets its own dwell-time and "
        "medium-utilisation conditions."
    ),
)

EUROPE = SpectrumRule(
    region="Avrupa (CEPT)",
    max_eirp_dbm=Sourced(
        20.0, "dBm", Provenance.STANDARD,
        "ETSI EN 300 328 V2.2.2, clause 4.3.2.2",
    ),
    max_eirp_density_dbm_per_mhz=Sourced(
        10.0, "dBm/MHz", Provenance.STANDARD,
        "ETSI EN 300 328 V2.2.2, wideband modulation other than FHSS",
    ),
    note="Identical in substance to the Turkish rule, which adopts it.",
)

UNITED_STATES = SpectrumRule(
    region="Amerika (FCC)",
    max_conducted_dbm=Sourced(
        30.0, "dBm", Provenance.STANDARD,
        "47 CFR 15.247(b)(3), one watt",
    ),
    antenna_gain_allowance_dbi=6.0,
    gain_payback_ratio=1.0,
    note=(
        "The limit is on conducted power, not radiated, and it assumes up "
        "to 6 dBi of antenna. Beyond that, power comes down decibel for "
        "decibel, so the radiated ceiling sits at 36 dBm. That is about "
        "21 dB above what Turkey allows at this bandwidth, and it is why "
        "range figures cannot be quoted without naming the region."
    ),
)

UNITED_STATES_POINT_TO_POINT = SpectrumRule(
    region="Amerika (FCC, sabit noktadan noktaya)",
    max_conducted_dbm=Sourced(
        30.0, "dBm", Provenance.STANDARD,
        "47 CFR 15.247(b)(3), one watt",
    ),
    antenna_gain_allowance_dbi=6.0,
    gain_payback_ratio=1.0 / 3.0,
    note=(
        "47 CFR 15.247(c)(1) lets a fixed point-to-point link pay back "
        "only one decibel of power for every three decibels of gain above "
        "6 dBi. Anchor to anchor backhaul could qualify; a link to a "
        "moving vehicle cannot, because it is not point to point."
    ),
)

LICENSED_ASSIGNMENT = SpectrumRule(
    region="Lisanslı tahsis",
    note=(
        "No licence-exempt ceiling, because the operator holds an "
        "assignment. Modelled as the hardware's own maximum. Whether a "
        "road authority can obtain one is a policy question this project "
        "cannot answer, so this region exists to show what the hardware "
        "would do rather than to propose it."
    ),
)

#: What a UWB device in a road or rail vehicle may radiate upward.
#:
#: Above the plane of the device's own mounting height, emissions outside
#: the vehicle stay at or under -53,3 dBm/MHz in 6-8,5 GHz, whether or not
#: the device has LDC or TPC. Below that plane -41,3 dBm/MHz holds.
VEHICLE_UWB_EXTERIOR_LIMIT = Sourced(
    -53.3, "dBm/MHz", Provenance.STANDARD,
    "ETSI EN 302 065-3 V2.1.1, 4.3.4.2 and table 4; BTK teknik ölçütler, "
    "Madde 18(2), Tablo 17",
)


def vehicle_uwb_ceiling_dbm(radio) -> Optional[float]:
    """The upward e.i.r.p. a vehicle's UWB radio may use, over its channel.

    Nothing for a radio that is not UWB: the rule is about ultra-wideband
    devices only. The radio's rating is already an emission limit, marked
    by its unit, so the ceiling is the limit's density over the channel.
    """
    if not radio.max_output_dbm.unit.endswith("/MHz"):
        return None
    channel_mhz = float(radio.ranging_bandwidth_hz.value) / 1e6
    return float(VEHICLE_UWB_EXTERIOR_LIMIT.value) + 10.0 * math.log10(channel_mhz)


REGIONS = {
    "TR": TURKEY,
    "TR-FHSS": TURKEY_FREQUENCY_HOPPING,
    "EU": EUROPE,
    "US": UNITED_STATES,
    "US-PTP": UNITED_STATES_POINT_TO_POINT,
    "LICENSED": LICENSED_ASSIGNMENT,
}
