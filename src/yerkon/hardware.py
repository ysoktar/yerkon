"""The parts the YERKON report actually names, with their published figures.

Everything here traces to the bill of materials on page 14 of the report or
to the manufacturer's datasheet for a part named there. Nothing is a
stand-in for a part the report did not choose, and no antenna is better
than the one in the bill.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from yerkon.evidence import Provenance, Sourced
from yerkon.settings import DEFAULTS, Settings

SPEED_OF_LIGHT_M_S = 299792458.0


@dataclass(frozen=True)
class Antenna:
    """A radiating element, described by what a link budget needs."""

    part: str
    peak_gain_dbi: Sourced
    efficiency: Sourced
    centre_frequency_hz: float
    bandwidth_hz: float

    def gain_dbi(self, elevation_deg: float = 0.0) -> float:
        """Gain toward a direction, in dBi.

        A printed antenna radiates in a torus around its plane rather than
        a sphere. Peak gain applies near the horizon, which is where the
        long links live, and falls off steeply overhead. The cosine shape
        below is the simplest form that gets that right; it is an
        approximation of a published pattern, not a measurement of one.
        """
        import math

        if not -90.0 <= elevation_deg <= 90.0:
            raise ValueError("elevation_deg must be within +/- 90")
        shape = math.cos(math.radians(elevation_deg)) ** 2
        floor_db = -20.0
        if shape <= 0.0:
            return float(self.peak_gain_dbi.value) + floor_db
        return float(self.peak_gain_dbi.value) + max(
            floor_db, 10.0 * math.log10(shape)
        )


@dataclass(frozen=True)
class Radio:
    """A transceiver, described by what decides whether a link closes."""

    part: str
    max_output_dbm: Sourced
    sensitivity_dbm: Sourced
    noise_figure_db: Sourced
    #: Occupied bandwidth of the ranging waveform, in Hz.
    ranging_bandwidth_hz: Sourced
    #: Correlation gain the receiver recovers, in dB. A spread waveform
    #: works below the noise floor; an impulse radio does not spread.
    processing_gain_db: Sourced
    #: Lowest signal-to-noise ratio at which the receiver still
    #: demodulates.
    demodulation_threshold_db: Sourced
    #: Whether that threshold is quoted on the ratio in the occupied
    #: bandwidth, or on the ratio after the receiver's correlation gain.
    #:
    #: The two conventions differ by the whole of the processing gain,
    #: which is thirty decibels, and getting it wrong grants a link that
    #: gain twice. A LoRa datasheet's "-20 dB" is in-band: despreading is
    #: what makes it workable and is already assumed in the figure. An
    #: impulse radio's working point is quoted after accumulation,
    #: because there is no spreading to assume.
    #:
    #: See ADR-0017. The first version of this model added the gain to
    #: both and let the SX1280 close a link twenty-four decibels below
    #: its own sensitivity.
    threshold_is_in_band: bool
    #: Duration of one waveform symbol, in seconds.
    #:
    #: For a spread waveform this is the chip sequence; for an impulse
    #: radio it is one preamble symbol. Either way it is what a frame's
    #: length is counted in, and a ranging exchange's duration decides
    #: both how often a receiver can be updated and how much clock offset
    #: accumulates while it waits for a reply.
    symbol_duration_s: Sourced
    #: Symbols in the ranging frame's preamble.
    #:
    #: The same number the processing gain comes from. Keeping them apart
    #: would let a change to one silently contradict the other.
    preamble_symbols: Sourced
    #: Best ranging precision the part reaches in practice, one sigma, in
    #: metres, however good the signal gets.
    #:
    #: The Cramer-Rao bound is a floor on what the waveform permits, and
    #: real receivers sit well above it: at 100 m the bound says the
    #: SX1280 could time an arrival to 2 cm, while the published
    #: measurements of that part scatter by about 3 m. The gap is clock
    #: resolution, the vendor's undisclosed estimator, and antenna group
    #: delay. Without this term the model would claim centimetre ranging
    #: from a narrowband radio.
    implementation_floor_m: Sourced
    #: Mean of the positive bias a blocked path adds to a range, in
    #: metres. With no direct ray, the first energy to arrive came the
    #: long way round, and this part's timing locks onto it. Drawn from
    #: an exponential distribution per exchange. None or zero is off
    #: (ADR-0084).
    nlos_bias_mean_m: Optional[Sourced] = None

    @property
    def nlos_bias_m(self) -> float:
        """The mean as a number, zero where it is not set."""
        if self.nlos_bias_mean_m is None:
            return 0.0
        return float(self.nlos_bias_mean_m.value)

    @property
    def rms_bandwidth_hz(self) -> float:
        """Root-mean-square bandwidth, which sets timing resolution.

        Time-of-arrival precision depends on the second moment of the
        spectrum rather than its width. For a waveform with a flat
        spectrum of width B this is B/sqrt(12).
        """
        import math

        return float(self.ranging_bandwidth_hz.value) / math.sqrt(12.0)


# --- Antennas -------------------------------------------------------------

W24P_U = Antenna(
    part="Inventek W24P-U",
    peak_gain_dbi=Sourced(
        3.2, "dBi", Provenance.DATASHEET,
        "Inventek W24P-U 2.4 GHz antenna specification, DOC-DS-20075",
    ),
    efficiency=Sourced(
        0.79, "fraction", Provenance.DATASHEET,
        "Inventek W24P-U 2.4 GHz antenna specification, DOC-DS-20075",
    ),
    centre_frequency_hz=2442e6,
    bandwidth_hz=100e6,
)
"""The printed antenna the report's bill of materials names."""


# --- Radios ---------------------------------------------------------------

def _sx1280_family(
    part: str, max_output_dbm: float, output_source: str,
    settings: Settings = DEFAULTS,
) -> Radio:
    """Both SX1280 variants in the bill differ only in output power."""
    return Radio(
        part=part,
        max_output_dbm=Sourced(
            max_output_dbm, "dBm", Provenance.DATASHEET, output_source
        ),
        sensitivity_dbm=Sourced(
            -132.0, "dBm", Provenance.DATASHEET,
            "Semtech SX1280 datasheet, best-case LoRa sensitivity; the "
            "module only carries the chip",
        ),
        noise_figure_db=settings.sourced("radio.sx1280.noise_figure_db"),
        ranging_bandwidth_hz=Sourced(
            1625e3, "Hz", Provenance.DATASHEET,
            "SX1280 datasheet, widest of the four LoRa bandwidths",
        ),
        processing_gain_db=Sourced(
            30.1, "dB", Provenance.DERIVED,
            "10*log10(2^10) for the SF10 ranging mode",
        ),
        demodulation_threshold_db=Sourced(
            -20.0, "dB", Provenance.DATASHEET,
            "SX1280 datasheet, SF10 demodulation floor relative to noise",
            note=(
                "Quoted in the occupied bandwidth. LoRa works below the "
                "noise because despreading lifts it, and that is what "
                "this figure already allows for."
            ),
        ),
        threshold_is_in_band=True,
        symbol_duration_s=Sourced(
            2 ** 10 / 1625e3, "s", Provenance.DERIVED,
            "2^SF / bandwidth at SF10 and 1625 kHz",
            note=(
                "630 microseconds. Three orders of magnitude longer than "
                "the impulse radio's symbol, which is why the two parts "
                "behave nothing alike once a reply delay is involved."
            ),
        ),
        preamble_symbols=Sourced(
            12.0, "symbols", Provenance.DATASHEET,
            "SX1280 datasheet, default LoRa preamble length",
        ),
        implementation_floor_m=Sourced(
            2.94, "m", Provenance.MEASUREMENT,
            "Stuart Robinson, SX1280 ranging trials over 0-250 m",
            note=(
                "Six published points at one configuration. The only "
                "figure in this project measured on the actual part."
            ),
        ),
        nlos_bias_mean_m=settings.sourced("radio.sx1280.nlos_bias_mean_m"),
    )


def radios(settings: Settings = DEFAULTS) -> dict:
    """The three modules the bill of materials names, from a settings file.

    The published figures are written here because they are published.
    The two that are not — a noise figure and a demodulation threshold —
    come from the settings file like every other figure nobody supplied.
    """
    urban = _sx1280_family(
        "Semtech SX1280 (EBYTE E28-2G4M12S)", 12.5,
        "EBYTE E28-2G4M12S user manual, maximum output power",
        settings,
    )
    rural = _sx1280_family(
        "EBYTE E28-2G4M27S", 27.0,
        "EBYTE E28-2G4M27S product page, rated output power",
        settings,
    )
    from dataclasses import replace as _replace

    tunnel = _replace(
        DWM3000,
        noise_figure_db=settings.sourced("radio.dwm3000.noise_figure_db"),
        demodulation_threshold_db=settings.sourced(
            "radio.dwm3000.demodulation_threshold_db"
        ),
        nlos_bias_mean_m=settings.sourced("radio.dwm3000.nlos_bias_mean_m"),
    )
    return {"sx1280": urban, "e28": rural, "dwm3000": tunnel}


SX1280 = _sx1280_family(
    "Semtech SX1280 (EBYTE E28-2G4M12S)",
    12.5,
    "EBYTE E28-2G4M12S user manual, maximum output power",
)
"""The town's and the open country's anchor radio, and the one in both
receivers.

It was an RF Solutions LAMBDA80-24S at 16,49 USD. The EBYTE module
carries the same Semtech chip at the same 12,5 dBm for 4,39 USD, so
nothing a link budget reads changes (ADR-0079)."""

E28_2G4M27S = _sx1280_family(
    "EBYTE E28-2G4M27S",
    27.0,
    "EBYTE E28-2G4M27S product page, rated output power",
)
"""The same silicon behind a power amplifier.

No row uses it any more. In Turkey the density limit caps radiated power
at 12,1 dBm at the ranging bandwidth, which the plain module already
reaches, so the amplifier's 27 dBm cannot be used there. Under rules
that allow it, the United States', it still can, which is why the
design tool keeps it (ADR-0079)."""

DWM3000 = Radio(
    part="Qorvo DWM3000",
    max_output_dbm=Sourced(
        -14.0, "dBm/MHz", Provenance.STANDARD,
        "IEEE 802.15.4z / FCC ultra-wideband emission limit",
    ),
    sensitivity_dbm=Sourced(
        -93.0, "dBm", Provenance.DATASHEET,
        "Qorvo DW3000 datasheet, channel 5 at 6.8 Mbps",
    ),
    noise_figure_db=DEFAULTS.sourced("radio.dwm3000.noise_figure_db"),
    nlos_bias_mean_m=DEFAULTS.sourced("radio.dwm3000.nlos_bias_mean_m"),
    ranging_bandwidth_hz=Sourced(
        499.2e6, "Hz", Provenance.DATASHEET,
        "IEEE 802.15.4z HRP channel 5 bandwidth",
    ),
    processing_gain_db=Sourced(
        30.1, "dB", Provenance.DERIVED,
        "10*log10(1024) for a 1024-symbol ranging preamble",
        note=(
            "An impulse radio does not spread a symbol, but it does "
            "accumulate the ranging preamble coherently, and that is where "
            "its margin below the thermal floor comes from. Without this "
            "term the budget says a 100 m UWB link cannot close, which "
            "contradicts every deployed system."
        ),
    ),
    symbol_duration_s=Sourced(
        1017.63e-9, "s", Provenance.STANDARD,
        "IEEE 802.15.4z HRP preamble symbol at 64 MHz pulse repetition",
    ),
    preamble_symbols=Sourced(
        1024.0, "symbols", Provenance.DATASHEET,
        "Qorvo DW3000, long ranging preamble",
        note=(
            "The same 1024 symbols the processing gain is taken over. A "
            "millisecond of preamble is what buys 30 dB, and it is also "
            "what makes the frame long."
        ),
    ),
    demodulation_threshold_db=DEFAULTS.sourced(
        "radio.dwm3000.demodulation_threshold_db"
    ),
    # An impulse radio does not spread a symbol, so its working point is
    # quoted after the preamble accumulation rather than before it.
    threshold_is_in_band=False,
    implementation_floor_m=Sourced(
        0.10, "m", Provenance.DATASHEET,
        "Qorvo DW3000 datasheet, stated ranging accuracy class",
    ),
)
"""The tunnel anchor's radio, and the short-range radio in both receivers."""
