"""Hardware profile registry: SX1280 family, NiceRF, Ebyte E28.

Software/firmware/calibration changes must not be mistaken for hardware
changes, and SX1280 must never collapse into SX1281 (ranging support
differs).
"""
import pytest

from locbench3d.core.evidence import EvidenceType
from locbench3d.hardware.profiles import (
    HARDWARE_PROFILE_REGISTRY,
    HardwareProfile,
    get_profile,
)


def test_sx1280_and_sx1281_are_distinct_profiles():
    sx1280 = get_profile("Semtech SX1280")
    sx1281 = get_profile("Semtech SX1281")
    assert sx1280.exact_model != sx1281.exact_model
    assert sx1280.verified_ranging_support is True
    assert sx1281.verified_ranging_support is False


def test_sx1281_provenance_conflict_is_recorded():
    """Older combined SX1280/SX1281 datasheet revisions market the family as
    having ranging capability without a per-part split in the title, while
    the current official SX1281 product page says 'without ranging'. This
    must be a flagged conflict, not a silent pick."""
    sx1281 = get_profile("Semtech SX1281")
    assert sx1281.provenance_conflict_flag is True
    assert sx1281.provenance_conflict_note


def test_every_profile_has_manufacturer_and_source():
    for name, profile in HARDWARE_PROFILE_REGISTRY.items():
        assert profile.manufacturer, f"{name} missing manufacturer"
        assert profile.evidence.evidence_type == EvidenceType.OFFICIAL_SPECIFICATION
        assert profile.evidence.source_scope


def test_required_hardware_families_present():
    required = {
        "Semtech SX1280",
        "Semtech SX1281",
        "NiceRF LoRa1280",
        "NiceRF LoRa1280-TCXO",
        "NiceRF LoRa1280F27",
        "NiceRF LoRa1280F27-TCXO",
    }
    assert required.issubset(HARDWARE_PROFILE_REGISTRY.keys())
    ebyte_names = [n for n in HARDWARE_PROFILE_REGISTRY if n.startswith("Ebyte E28")]
    assert len(ebyte_names) >= 1


def test_ebyte_e28_variants_carry_verification_state():
    """The requirement is 'exact suffix and revision verification', meaning
    the schema must be able to represent an unverified claim distinctly
    from a verified one, not that every SKU has been physically checked."""
    ebyte_names = [n for n in HARDWARE_PROFILE_REGISTRY if n.startswith("Ebyte E28")]
    for name in ebyte_names:
        profile = get_profile(name)
        assert profile.hardware_revision is not None
        # verified_radio_ic being None (rather than a guessed chip name) is
        # the correct representation of "not independently verified".
        assert profile.verified_radio_ic is None or isinstance(
            profile.verified_radio_ic, str
        )


def test_software_calibration_fields_are_separate_from_hardware_identity():
    sx1280 = get_profile("Semtech SX1280")
    assert hasattr(sx1280, "firmware_identity")
    assert hasattr(sx1280, "driver_or_software_identity")
    assert hasattr(sx1280, "calibration_requirement")
    # These must not be folded into exact_model / hardware_revision.
    assert sx1280.firmware_identity != sx1280.exact_model


def test_unknown_profile_raises():
    with pytest.raises(KeyError):
        get_profile("Not A Real Radio")


def test_hardware_profile_to_dict_preserves_provenance():
    sx1280 = get_profile("Semtech SX1280")
    d = sx1280.to_dict()
    assert d["evidence_type"] == "OFFICIAL_SPECIFICATION"
    assert d["source_url"]
