"""What Turkish and CEPT spectrum rules allow in the 2.4 GHz band.

The report picks the SX1280 and, for the rural corridor, a 27 dBm module
built around it. Neither choice is free: 2400-2483.5 MHz is licence-exempt
in Turkey only within stated limits, and those limits turn out to decide
two things the report leaves open.

The first is the ranging bandwidth. The SX1280 offers four, and the
density cap makes the choice one-sided: because the legal transmit power
scales with occupied bandwidth, and thermal noise scales with it too, a
wider ranging bandwidth costs nothing in link budget while buying timing
resolution proportionally. See ``psd_limited_power_dbm``.

The second is the rural transmit power, and there the report has a
problem. See ``E28_COMPLIANCE``.

Sources are the harmonised standard and the Turkish implementation of it.
Turkey's regime follows CEPT/ERC REC 70-03 and cites TS EN 300 328
directly, so the two carry the same numbers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from yerkon.evidence import EvidenceRecord, EvidenceType

ETSI_URL = (
    "https://www.etsi.org/deliver/etsi_en/300300_300399/300328/"
    "02.02.02_60/en_300328v020202p.pdf"
)
BTK_KET_URL = "https://www.resmigazete.gov.tr/eskiler/2012/09/20120911-24.htm"

#: The licence-exempt band the SX1280 works in, in Hz.
ISM_BAND_HZ = (2400e6, 2483.5e6)

#: Total radiated power cap, dBm e.i.r.p. 100 mW.
MAX_EIRP_DBM = 20.0

#: Density cap for non-FHSS wideband modulation, dBm e.i.r.p. per MHz.
#: 10 mW/MHz. LoRa is not frequency hopping, so this is the applicable one.
MAX_EIRP_DENSITY_DBM_PER_MHZ = 10.0

#: The four LoRa bandwidths the SX1280 supports, in Hz.
SX1280_BANDWIDTHS_HZ = (203e3, 406e3, 812e3, 1625e3)

#: The bandwidth Robinson's published ranging work uses, in Hz. This is
#: why the 406 kHz simulation and his measurements agree: they are the
#: same configuration, not a coincidence.
ROBINSON_BANDWIDTH_HZ = 406e3

SPECTRUM_EVIDENCE = EvidenceRecord(
    evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
    source_name=(
        "ETSI EN 300 328 V2.2.2 wideband transmission systems, as adopted "
        "in Turkey through the BTK short-range device regulation (KET)"
    ),
    source_url=ETSI_URL,
    source_scope=(
        "2400-2483.5 MHz licence-exempt operation: 20 dBm e.i.r.p. total "
        "and 10 dBm/MHz e.i.r.p. density for modulation other than FHSS. "
        "Turkey's KET regulation cites TS EN 300 328 and carries the same "
        "two limits (100 mW e.i.r.p., 10 mW/MHz for non-FHSS wideband)."
    ),
    caveats=(
        "The Turkish figures were read from secondary summaries of the KET "
        "regulation and its BTK annex; the primary documents were not "
        "reachable from this project's network. They agree with the CEPT "
        "position Turkey harmonises with, but confirm against the BTK "
        "annex before quoting them in a submission. Licence-exempt limits "
        "are also not the only route: a road authority may instead hold a "
        "frequency assignment, under which they do not apply."
    ),
)


def psd_limited_power_dbm(bandwidth_hz: float) -> float:
    """Highest legal e.i.r.p. at a given occupied bandwidth, in dBm.

    Two caps apply and the lower one wins. The density cap is the binding
    one at every SX1280 bandwidth, so in practice this returns
    ``10 + 10*log10(BW in MHz)``: 3.1 dBm at 203 kHz up to 12.1 dBm at
    1625 kHz. Published SX1280 localisation deployments run 1625 kHz at
    12 dBm, which is this limit to within rounding.
    """
    if bandwidth_hz <= 0:
        raise ValueError("bandwidth_hz must be positive")
    density_limited = MAX_EIRP_DENSITY_DBM_PER_MHZ + 10.0 * math.log10(
        bandwidth_hz / 1e6
    )
    return min(MAX_EIRP_DBM, density_limited)


def bandwidth_is_snr_neutral() -> bool:
    """Whether changing SX1280 bandwidth changes the received SNR.

    It does not, and this is the reason the bandwidth choice is one-sided.
    Under the density cap the legal transmit power rises with bandwidth by
    ``10*log10(B)``. Thermal noise in the receiver rises by the same
    ``10*log10(B)``. The two cancel, so the SNR at a given distance is
    unchanged and the link reaches as far at 1625 kHz as at 203 kHz, while
    timing resolution improves in proportion to bandwidth.

    Stated as a function because it is an assertion about the model, and
    ``tests/test_regulatory.py`` checks it against the arithmetic rather
    than letting it sit in a docstring as a claim.
    """
    return True


@dataclass(frozen=True)
class ComplianceFinding:
    """A configuration in the report checked against the limits above."""

    subject: str
    conducted_power_dbm: float
    limit_dbm: float
    evidence: EvidenceRecord

    @property
    def excess_db(self) -> float:
        return self.conducted_power_dbm - self.limit_dbm

    @property
    def compliant(self) -> bool:
        return self.excess_db <= 0.0


E28_COMPLIANCE = ComplianceFinding(
    subject="EBYTE E28-2G4M27S at 27 dBm, rural corridor",
    conducted_power_dbm=27.0,
    limit_dbm=MAX_EIRP_DBM,
    evidence=EvidenceRecord(
        evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
        source_name="E28-2G4M27S rated output against EN 300 328 / KET limits",
        source_url=BTK_KET_URL,
        source_scope=(
            "The module is rated 27 dBm (500 mW) conducted. The licence-exempt "
            "cap is 20 dBm e.i.r.p. total, and 10 dBm/MHz density puts a "
            "1625 kHz ranging signal at 12.1 dBm. e.i.r.p. includes antenna "
            "gain, so a 5 dBi antenna raises the conducted figure further "
            "rather than offsetting it."
        ),
        caveats=(
            "The module is sold legally; the rating is what the hardware can "
            "do, not a claim about where it may be operated at that setting. "
            "Regions differ, and the part is usable in Turkey at a reduced "
            "setting. The finding is about the 8 km reference distance the "
            "rural range is derived from, which is quoted at the full 27 dBm."
        ),
    ),
)

#: How far the rural link reaches once the power is brought inside the
#: licence-exempt cap, expressed as the exponent-dependent shrink factor.
#: Free space is n=2; a highway verge with vegetation and terrain sits
#: nearer n=2.7, which is what ``RURAL_LINK_RANGE`` already assumes.
RURAL_PATH_LOSS_EXPONENT = 2.7


def range_scale_for_power_cut(excess_db: float, exponent: float) -> float:
    """Fraction of the original range left after giving up ``excess_db``.

    Range goes as ``10 ** (-excess / (10 * n))`` for path loss exponent
    ``n``. At n=2.7 and 14.9 dB of excess this is 0.28, so a reference
    distance quoted at 27 dBm covers about a quarter of that once the
    transmitter is legal at 12.1 dBm.
    """
    if exponent <= 0:
        raise ValueError("exponent must be positive")
    return float(10.0 ** (-excess_db / (10.0 * exponent)))
