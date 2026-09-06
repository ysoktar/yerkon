"""Official and primary reference sources cited by this benchmark.

Network egress to manufacturer/standards/agency web pages was blocked in
the environment this project was built in (see docs/LIMITATIONS.md); most
entries below are the URLs and general claims from the requirements
document and general domain knowledge, not a fresh page fetch. Two facts
were independently checked this session via search-engine snippets
(``verified_this_session=True``): the current SX1281 product page title
("2.4GHz Without Ranging") and the GPS.gov signal-in-space vs
receiver-accuracy distinction. Everything else here needs a manual check
against the live page before being treated as authoritative for a
specific numeric claim.
"""
from __future__ import annotations

from dataclasses import dataclass

from locbench3d.core.evidence import EvidenceRecord, EvidenceType


@dataclass(frozen=True)
class OfficialSource:
    topic: str
    evidence: EvidenceRecord
    verified_this_session: bool
    note: str = ""


_NOT_VERIFIED_CAVEAT = (
    "Not freshly fetched in this build session (network egress to this "
    "domain was blocked); verify against the live page before relying on "
    "a specific numeric claim from it."
)

OFFICIAL_SOURCES: list[OfficialSource] = [
    OfficialSource(
        topic="Semtech SX1280 (ranging-capable 2.4 GHz transceiver)",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="Semtech SX1280 product page",
            source_url="https://www.semtech.com/products/wireless-rf/lora-connect/sx1280",
            source_scope="Manufacturer product page for the SX1280 IC. " + _NOT_VERIFIED_CAVEAT,
        ),
        verified_this_session=False,
    ),
    OfficialSource(
        topic="Semtech SX1281 (2.4 GHz transceiver without ranging)",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="Semtech SX1281 product page",
            source_url="https://www.semtech.com/products/wireless-rf/lora-connect/sx1281",
            source_scope=(
                "Current product-page title, confirmed via search-engine "
                "snippet this session: 'LoRa Connect Transceiver, SX1281, "
                "2.4GHz Without Ranging'. See the provenance_conflict fields "
                "on the SX1281 hardware profile for how this differs from "
                "older shared-datasheet titles."
            ),
        ),
        verified_this_session=True,
    ),
    OfficialSource(
        topic="Semtech ranging FAQ",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="Semtech ranging FAQ (P40)",
            source_url="https://www.semtech.com/design-support/faq/P40",
            source_scope="Manufacturer FAQ on ranging operation. " + _NOT_VERIFIED_CAVEAT,
        ),
        verified_this_session=False,
    ),
    OfficialSource(
        topic="IEEE 802.15.4 (UWB PHY standard)",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="IEEE 802.15.4 standard page",
            source_url="https://standards.ieee.org/ieee/802.15.4/11041/",
            source_scope="Standards body page, not the standard text itself. " + _NOT_VERIFIED_CAVEAT,
        ),
        verified_this_session=False,
    ),
    OfficialSource(
        topic="GPS performance",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="GPS.gov, GPS performance",
            source_url="https://www.gps.gov/gps-performance",
            source_scope="Official GPS.gov performance summary. " + _NOT_VERIFIED_CAVEAT,
        ),
        verified_this_session=False,
    ),
    OfficialSource(
        topic="GPS accuracy (signal-in-space vs user/receiver accuracy)",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="GPS.gov, GPS accuracy",
            source_url="https://www.gps.gov/gps-accuracy",
            source_scope=(
                "Confirmed via search-engine snippet this session: GPS.gov "
                "commits to a daily global average signal-in-space user "
                "range error (URE) <= 2.0 m at 95% probability, distinct "
                "from receiver/user position accuracy which also depends on "
                "geometry and local conditions. This project keeps "
                "signal-in-space error and user-position error as separate "
                "fields for exactly this reason."
            ),
        ),
        verified_this_session=True,
    ),
    OfficialSource(
        topic="BeiDou",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="China Satellite Navigation Office, BeiDou",
            source_url="https://en.beidou.gov.cn/",
            source_scope="Official BeiDou program site. " + _NOT_VERIFIED_CAVEAT,
        ),
        verified_this_session=False,
    ),
    OfficialSource(
        topic="Galileo",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="European GNSS Service Centre, Galileo",
            source_url="https://www.gsc-europa.eu/",
            source_scope="Official Galileo service centre site. " + _NOT_VERIFIED_CAVEAT,
        ),
        verified_this_session=False,
    ),
    OfficialSource(
        topic="QZSS",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="Cabinet Office, QZSS",
            source_url="https://qzss.go.jp/en/",
            source_scope="Official QZSS program site. " + _NOT_VERIFIED_CAVEAT,
        ),
        verified_this_session=False,
    ),
    OfficialSource(
        topic="NavIC",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="ISRO, NavIC",
            source_url="https://www.isro.gov.in/",
            source_scope="Official ISRO site. " + _NOT_VERIFIED_CAVEAT,
        ),
        verified_this_session=False,
    ),
    OfficialSource(
        topic="Android Wi-Fi RTT (802.11mc FTM)",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="Android Developers, Wi-Fi RTT",
            source_url="https://developer.android.com/develop/connectivity/wifi/wifi-rtt",
            source_scope="Official Android developer documentation. " + _NOT_VERIFIED_CAVEAT,
        ),
        verified_this_session=False,
    ),
    OfficialSource(
        topic="MATLAB UWB toolbox",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.SOFTWARE_REFERENCE,
            source_name="MathWorks, UWB (Communications Toolbox)",
            source_url="https://www.mathworks.com/help/comm/uwb.html",
            source_scope=(
                "Official MathWorks documentation for MATLAB-based UWB "
                "waveform generation/analysis. " + _NOT_VERIFIED_CAVEAT
            ),
        ),
        verified_this_session=False,
    ),
]
