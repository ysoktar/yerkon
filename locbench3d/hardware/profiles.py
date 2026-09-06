"""Hardware profile registry for 2.4 GHz ranging-capable radios.

Every profile keeps claimed vs. verified fields separate, because a
manufacturer's marketing claim and an independently verified fact are not
the same evidence. Where this project has not independently verified a
fact in this session (for example, by opening the current datasheet PDF or
inspecting real hardware), the verified field is left ``None`` rather than
filled with a guessed value.

Software identity (firmware, driver), and calibration requirements are
kept as separate fields from hardware identity (exact model, hardware
revision) so a firmware or calibration change is never mistaken for a
hardware change.

Network access to manufacturer and distributor pages was blocked in the
environment this registry was built in (see docs/LIMITATIONS.md). Values
below come from the SX1280/SX1281 datasheet family and Semtech's product
pages as known at the time of writing, plus search-snippet confirmation of
the current SX1281 product page title; they have not been re-fetched and
diffed against the live page in this session. Numeric fields the author
was not confident of from memory (exact TX power range, exact sensitivity
figures per data rate) are left ``None`` rather than guessed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from locbench3d.core.evidence import EvidenceRecord, EvidenceType


@dataclass(frozen=True)
class HardwareProfile:
    manufacturer: str
    module_family: str
    exact_model: str
    hardware_revision: Optional[str]
    claimed_radio_ic: Optional[str]
    verified_radio_ic: Optional[str]
    claimed_ranging_support: Optional[bool]
    verified_ranging_support: Optional[bool]
    operating_band: Optional[str]
    bandwidth_options_khz: Optional[tuple[float, ...]]
    max_tx_power_dbm: Optional[float]
    rx_sensitivity_dbm: Optional[float]
    oscillator_type: Optional[str]
    oscillator_tolerance_ppm: Optional[float]
    pa_present: Optional[bool]
    lna_present: Optional[bool]
    tx_current_ma: Optional[float]
    rx_current_ma: Optional[float]
    sleep_current_ua: Optional[float]
    calibration_requirement: Optional[str]
    firmware_identity: Optional[str]
    driver_or_software_identity: Optional[str]
    evidence: EvidenceRecord
    provenance_conflict_flag: bool = False
    provenance_conflict_note: str = ""

    def to_dict(self) -> dict:
        d = {
            "manufacturer": self.manufacturer,
            "module_family": self.module_family,
            "exact_model": self.exact_model,
            "hardware_revision": self.hardware_revision,
            "claimed_radio_ic": self.claimed_radio_ic,
            "verified_radio_ic": self.verified_radio_ic,
            "claimed_ranging_support": self.claimed_ranging_support,
            "verified_ranging_support": self.verified_ranging_support,
            "operating_band": self.operating_band,
            "bandwidth_options_khz": self.bandwidth_options_khz,
            "max_tx_power_dbm": self.max_tx_power_dbm,
            "rx_sensitivity_dbm": self.rx_sensitivity_dbm,
            "oscillator_type": self.oscillator_type,
            "oscillator_tolerance_ppm": self.oscillator_tolerance_ppm,
            "pa_present": self.pa_present,
            "lna_present": self.lna_present,
            "tx_current_ma": self.tx_current_ma,
            "rx_current_ma": self.rx_current_ma,
            "sleep_current_ua": self.sleep_current_ua,
            "calibration_requirement": self.calibration_requirement,
            "firmware_identity": self.firmware_identity,
            "driver_or_software_identity": self.driver_or_software_identity,
            "provenance_conflict_flag": self.provenance_conflict_flag,
            "provenance_conflict_note": self.provenance_conflict_note,
        }
        d.update(self.evidence.to_dict())
        return d


_SEMTECH_SCOPE = (
    "Manufacturer datasheet and product-page claims for the bare radio IC. "
    "Not a project measurement. Numeric fields left as None were not "
    "confirmed against a freshly fetched datasheet in this session "
    "(network egress to manufacturer/distributor sites was blocked in the "
    "build environment); verify before relying on them."
)

HARDWARE_PROFILE_REGISTRY: dict[str, HardwareProfile] = {
    "Semtech SX1280": HardwareProfile(
        manufacturer="Semtech",
        module_family="SX1280/SX1281 family",
        exact_model="SX1280",
        hardware_revision=None,
        claimed_radio_ic="SX1280",
        verified_radio_ic="SX1280",
        claimed_ranging_support=True,
        verified_ranging_support=True,
        operating_band="2400-2483.5 MHz ISM",
        bandwidth_options_khz=(203.125, 406.25, 812.5, 1625.0),
        max_tx_power_dbm=None,
        rx_sensitivity_dbm=None,
        oscillator_type="TCXO or crystal, per application design",
        oscillator_tolerance_ppm=None,
        pa_present=None,
        lna_present=None,
        tx_current_ma=None,
        rx_current_ma=None,
        sleep_current_ua=None,
        calibration_requirement=(
            "Ranging distance offset calibration recommended per module/antenna "
            "combination; see Semtech ranging FAQ P40."
        ),
        firmware_identity=None,
        driver_or_software_identity=None,
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="Semtech SX1280 product page",
            source_url="https://www.semtech.com/products/wireless-rf/lora-connect/sx1280",
            source_scope=_SEMTECH_SCOPE,
        ),
    ),
    "Semtech SX1281": HardwareProfile(
        manufacturer="Semtech",
        module_family="SX1280/SX1281 family",
        exact_model="SX1281",
        hardware_revision=None,
        claimed_radio_ic="SX1281",
        verified_radio_ic="SX1281",
        claimed_ranging_support=False,
        verified_ranging_support=False,
        operating_band="2400-2483.5 MHz ISM",
        bandwidth_options_khz=(203.125, 406.25, 812.5, 1625.0),
        max_tx_power_dbm=None,
        rx_sensitivity_dbm=None,
        oscillator_type="TCXO or crystal, per application design",
        oscillator_tolerance_ppm=None,
        pa_present=None,
        lna_present=None,
        tx_current_ma=None,
        rx_current_ma=None,
        sleep_current_ua=None,
        calibration_requirement=None,
        firmware_identity=None,
        driver_or_software_identity=None,
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name="Semtech SX1281 product page",
            source_url="https://www.semtech.com/products/wireless-rf/lora-connect/sx1281",
            source_scope=_SEMTECH_SCOPE
            + " Current product-page title is 'LoRa Connect Transceiver, "
            "SX1281, 2.4GHz Without Ranging'.",
        ),
        provenance_conflict_flag=True,
        provenance_conflict_note=(
            "Shared SX1280/SX1281(/SX1282) datasheet revisions (e.g. Rev 1.1, "
            "Rev 2.2, Rev 3.0, Rev 3.2) are titled 'Long Range, Low Power, "
            "2.4GHz Transceiver with Ranging Capability' and describe a "
            "ranging engine at the family level, without a per-part ranging "
            "matrix visible from the title alone. The current Semtech "
            "SX1281 product page instead titles the part '2.4GHz Without "
            "Ranging'. This benchmark follows the current product-page "
            "distinction (SX1281 = no native ranging) rather than the "
            "shared datasheet title, and flags the discrepancy rather than "
            "resolving it silently. Re-verify against the current datasheet "
            "revision's per-part feature table if this matters for a "
            "specific design decision."
        ),
    ),
}


def _nicerf_profile(
    exact_model: str,
    tcxo: bool,
    high_power: bool,
) -> HardwareProfile:
    scope = (
        "NiceRF module product-page/datasheet claim for a module built "
        "around the Semtech SX1280 IC. This project has not independently "
        "opened a NiceRF datasheet in this session (network egress to "
        "vendor sites was blocked); verified_radio_ic is left unset "
        "pending that check, distinct from the manufacturer's claim."
    )
    return HardwareProfile(
        manufacturer="NiceRF",
        module_family="LoRa1280 (SX1280-based)",
        exact_model=exact_model,
        hardware_revision=None,
        claimed_radio_ic="Semtech SX1280",
        verified_radio_ic=None,
        claimed_ranging_support=True,
        verified_ranging_support=None,
        operating_band="2400-2483.5 MHz ISM",
        bandwidth_options_khz=(203.125, 406.25, 812.5, 1625.0),
        max_tx_power_dbm=27.0 if high_power else None,
        rx_sensitivity_dbm=None,
        oscillator_type="TCXO" if tcxo else "crystal",
        oscillator_tolerance_ppm=0.5 if tcxo else None,
        pa_present=high_power,
        lna_present=None,
        tx_current_ma=None,
        rx_current_ma=None,
        sleep_current_ua=None,
        calibration_requirement=(
            "Ranging offset calibration recommended per module and antenna; "
            "vendor calibration procedure not independently verified this "
            "session."
        ),
        firmware_identity=None,
        driver_or_software_identity=None,
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name=f"NiceRF {exact_model} product claim",
            source_url="",
            source_scope=scope,
        ),
        provenance_conflict_flag=False,
        provenance_conflict_note=(
            "max_tx_power_dbm=27 dBm for F27 variants reflects the model "
            "name's common convention (Fxx = external PA rated dBm) and has "
            "not been independently confirmed against a fetched datasheet."
            if high_power
            else ""
        ),
    )


HARDWARE_PROFILE_REGISTRY["NiceRF LoRa1280"] = _nicerf_profile(
    "LoRa1280", tcxo=False, high_power=False
)
HARDWARE_PROFILE_REGISTRY["NiceRF LoRa1280-TCXO"] = _nicerf_profile(
    "LoRa1280-TCXO", tcxo=True, high_power=False
)
HARDWARE_PROFILE_REGISTRY["NiceRF LoRa1280F27"] = _nicerf_profile(
    "LoRa1280F27", tcxo=False, high_power=True
)
HARDWARE_PROFILE_REGISTRY["NiceRF LoRa1280F27-TCXO"] = _nicerf_profile(
    "LoRa1280F27-TCXO", tcxo=True, high_power=True
)


def _ebyte_e28_profile(exact_model: str, note: str) -> HardwareProfile:
    return HardwareProfile(
        manufacturer="Ebyte",
        module_family="E28 (SX1280-based)",
        exact_model=exact_model,
        hardware_revision="unverified",
        claimed_radio_ic="Semtech SX1280",
        verified_radio_ic=None,
        claimed_ranging_support=True,
        verified_ranging_support=None,
        operating_band="2400-2483.5 MHz ISM",
        bandwidth_options_khz=(203.125, 406.25, 812.5, 1625.0),
        max_tx_power_dbm=None,
        rx_sensitivity_dbm=None,
        oscillator_type=None,
        oscillator_tolerance_ppm=None,
        pa_present=None,
        lna_present=None,
        tx_current_ma=None,
        rx_current_ma=None,
        sleep_current_ua=None,
        calibration_requirement=None,
        firmware_identity=None,
        driver_or_software_identity=None,
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
            source_name=f"Ebyte {exact_model} product claim",
            source_url="",
            source_scope=(
                "Vendor model-family naming claim only. Ebyte sells multiple "
                "E28 suffix/revision variants across power levels and "
                "antenna interfaces; this project has not verified which "
                "exact suffix and hardware revision maps to which "
                "specification in this session. Treat exact_model as a "
                "placeholder family entry, not a confirmed SKU, until the "
                "exact suffix is checked against the current Ebyte "
                "datasheet for the unit in hand."
            ),
        ),
        provenance_conflict_flag=True,
        provenance_conflict_note=note,
    )


HARDWARE_PROFILE_REGISTRY["Ebyte E28 (SX1280, suffix unverified)"] = (
    _ebyte_e28_profile(
        "E28-2G4Mxxx (suffix unverified)",
        "Ebyte's E28 series spans multiple SX1280-based SKUs distinguished "
        "by TX power and connector suffix (e.g. -20S, -27S families in "
        "similar Ebyte product lines). The exact suffix and hardware "
        "revision must be read off the physical module or an order "
        "confirmation before its specifications are trusted; this registry "
        "entry exists to hold that record once verified, not to assert it.",
    )
)


def get_profile(name: str) -> HardwareProfile:
    if name not in HARDWARE_PROFILE_REGISTRY:
        raise KeyError(
            f"Unknown hardware profile {name!r}. "
            f"Known profiles: {sorted(HARDWARE_PROFILE_REGISTRY)}"
        )
    return HARDWARE_PROFILE_REGISTRY[name]


def list_profiles() -> list[str]:
    return sorted(HARDWARE_PROFILE_REGISTRY)
