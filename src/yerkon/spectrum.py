"""A recording of the band, turned into the packet loss the model assumes.

The urban row assumes that 15 % of ranging exchanges are lost to other
traffic in the 2,4 GHz band, and nothing measures that figure. A software
defined radio can: record the channel an anchor would use, at the place
it would stand, and count how often something else was on the air.

Two recorders are read, both free and both common:

* **SDR++**, whose recorder writes baseband as a WAV file with I in the
  left channel and Q in the right, as unsigned 8-bit, 16-bit or 32-bit
  integers or 32-bit floats. The centre frequency is not in the file;
  the default file name carries it (``..._2440000000Hz_...``).
* **SDRangel**, whose file sink writes ``.sdriq``: a 32-byte header
  (sample rate, centre frequency, start time in milliseconds, sample
  size, a filler word and a CRC-32 over the first 28 bytes), then I and
  Q interleaved as 16-bit integers, or as 32-bit integers when the
  sample size is 24.

Both layouts were read from the projects' own source (SDR++
``core/src/utils/wav.cpp`` and ``misc_modules/recorder``; SDRangel
``sdrbase/dsp/filerecord.{h,cpp}`` and ``dsptypes.h``), not assumed.

What is measured is deliberately simple and says what it assumes. The
recording is cut into short blocks; each block's power inside the
anchor's channel is compared with the channel's own quiet level; a block
more than ``threshold_db`` above it is busy. An exchange is lost when
any block it overlaps is busy, so the answer is the share of
exchange-long windows that touch a busy block. No model of the
interferer is needed, and the exchange length is the model's own.

What it does not know: how strong the wanted signal is. A link with a
large margin shrugs off an interferer that breaks a link at the edge of
coverage. The threshold stands in for that, and the default treats any
clear rise above the quiet level as a loss, which is the edge-of-coverage
case and so the pessimistic one (ADR-0083).
"""

from __future__ import annotations

import math
import pathlib
import re
import struct
import zlib
from dataclasses import dataclass
from typing import Optional

import numpy as np

#: How long one power block is, in seconds. Short against an exchange
#: (31,8 ms at SF10 and 1625 kHz) so that a burst is placed to within a
#: small fraction of it, long enough that a block holds hundreds of
#: frequency bins and its power reading is steady.
BLOCK_S = 0.0005

#: How far above the quiet level a block has to be to count as busy.
#:
#: Three decibels is a doubling of the channel's power: something else is
#: at least as loud as the noise. With hundreds of bins in a block the
#: power of pure noise scatters by a fraction of a decibel, so this does
#: not call noise busy.
DEFAULT_THRESHOLD_DB = 3.0

#: Which percentile of block power is taken as the quiet level. Low, so
#: that a channel busy most of the time still has its floor found; not
#: the minimum, which is one unlucky block.
QUIET_PERCENTILE = 10.0

#: Samples read at a time, so an hour-long recording does not have to fit
#: in memory.
CHUNK_BLOCKS = 4096


@dataclass(frozen=True)
class Recording:
    """IQ samples on disk, and what the file says about them."""

    path: pathlib.Path
    sample_rate_hz: float
    #: Where the recorder was tuned, where the file says so. SDR++ keeps
    #: it in the file name; SDRangel in the header.
    centre_hz: Optional[float]
    #: Interleaved I and Q, as the file stores them.
    samples: np.ndarray
    #: What to subtract before scaling, for unsigned samples.
    offset: float = 0.0

    @property
    def duration_s(self) -> float:
        return (len(self.samples) // 2) / self.sample_rate_hz

    def iq(self, start: int, count: int) -> np.ndarray:
        """``count`` complex samples from ``start``, as complex64."""
        raw = np.asarray(
            self.samples[2 * start: 2 * (start + count)], dtype=np.float32)
        raw = raw - self.offset
        return raw[0::2] + 1j * raw[1::2]


# --- Reading the two recorders --------------------------------------------


def read_sdrpp_wav(path) -> Recording:
    """A baseband WAV from SDR++'s recorder."""
    where = pathlib.Path(path)
    with open(where, "rb") as handle:
        head = handle.read(12)
        if len(head) < 12 or head[:4] != b"RIFF" or head[8:12] != b"WAVE":
            raise ValueError("{} is not a WAV file".format(where))
        fmt = None
        offset = 12
        while True:
            handle.seek(offset)
            chunk = handle.read(8)
            if len(chunk) < 8:
                raise ValueError("{} has no data chunk".format(where))
            name, size = chunk[:4], struct.unpack("<I", chunk[4:])[0]
            if name == b"fmt ":
                fmt = handle.read(size)
            elif name == b"data":
                data_at, data_size = offset + 8, size
                break
            offset += 8 + size + (size & 1)
    if fmt is None:
        raise ValueError("{} has no format chunk".format(where))
    codec, channels, rate, _, _, bits = struct.unpack("<HHIIHH", fmt[:16])
    if channels != 2:
        raise ValueError(
            "{} has {} channel(s). A baseband recording has two, I and Q; "
            "an audio recording is not what this reads.".format(where, channels))
    kinds = {(1, 8): (np.uint8, 128.0), (1, 16): (np.int16, 0.0),
             (1, 32): (np.int32, 0.0), (3, 32): (np.float32, 0.0)}
    if (codec, bits) not in kinds:
        raise ValueError("{}: codec {} at {} bits is not one SDR++ writes"
                         .format(where, codec, bits))
    kind, offset_value = kinds[(codec, bits)]
    count = data_size // np.dtype(kind).itemsize
    samples = np.memmap(where, dtype=kind, mode="r", offset=data_at,
                        shape=(count - count % 2,))
    return Recording(where, float(rate), _centre_from_name(where.name),
                     samples, offset_value)


def _centre_from_name(name: str) -> Optional[float]:
    """The ``..._2440000000Hz_...`` SDR++ puts in its default file names."""
    found = re.search(r"(\d+)Hz", name)
    return float(found.group(1)) if found else None


SDRIQ_HEADER = struct.Struct("<IQQIII")


def read_sdrangel_sdriq(path) -> Recording:
    """A ``.sdriq`` file from SDRangel's file sink."""
    where = pathlib.Path(path)
    with open(where, "rb") as handle:
        head = handle.read(SDRIQ_HEADER.size)
    if len(head) < SDRIQ_HEADER.size:
        raise ValueError("{} is shorter than an .sdriq header".format(where))
    rate, centre, _, sample_bits, _, crc = SDRIQ_HEADER.unpack(head)
    if zlib.crc32(head[:28]) & 0xFFFFFFFF != crc:
        raise ValueError(
            "{}: the header's checksum does not match. It is not an .sdriq "
            "file, or it was damaged.".format(where))
    kinds = {16: np.int16, 24: np.int32}
    if sample_bits not in kinds:
        raise ValueError("{}: sample size {} is not 16 or 24".format(
            where, sample_bits))
    kind = kinds[sample_bits]
    count = (where.stat().st_size - SDRIQ_HEADER.size) // np.dtype(kind).itemsize
    samples = np.memmap(where, dtype=kind, mode="r", offset=SDRIQ_HEADER.size,
                        shape=(count - count % 2,))
    return Recording(where, float(rate), float(centre), samples)


def read_recording(path) -> Recording:
    """Either recorder's file, by its extension."""
    suffix = pathlib.Path(path).suffix.lower()
    if suffix == ".wav":
        return read_sdrpp_wav(path)
    if suffix == ".sdriq":
        return read_sdrangel_sdriq(path)
    raise ValueError(
        "{} is neither an SDR++ baseband WAV nor an SDRangel .sdriq".format(path))


# --- What the recording says ----------------------------------------------


@dataclass(frozen=True)
class Occupancy:
    """How busy the channel was, and what that costs an exchange."""

    #: Share of blocks with something on the air.
    busy_share: float
    #: Share of exchange-long windows that touch a busy block: the
    #: probability that an exchange starting at a random moment is lost.
    exchange_loss: float
    exchange_s: float
    block_s: float
    blocks: int
    quiet_level: float
    threshold_db: float
    channel_hz: float
    offset_hz: float
    duration_s: float


def channel_power(recording: Recording, channel_hz: float,
                  offset_hz: float = 0.0, block_s: float = BLOCK_S) -> np.ndarray:
    """Power inside the channel, block by block, in the file's own units.

    Each block is transformed and the bins inside the channel summed, so
    traffic next to the channel, which the anchor's receiver filters out,
    does not count.
    """
    rate = recording.sample_rate_hz
    if channel_hz > rate:
        raise ValueError(
            "the recording is {:.3g} MHz wide and the channel {:.3g} MHz: "
            "record at a sample rate at least as wide as the channel".format(
                rate / 1e6, channel_hz / 1e6))
    size = max(int(round(block_s * rate)), 16)
    freqs = np.fft.fftfreq(size, d=1.0 / rate)
    inside = np.abs(freqs - offset_hz) <= channel_hz / 2.0
    if not inside.any():
        raise ValueError("no frequency bin falls inside the channel")
    total = (len(recording.samples) // 2) // size
    out = np.empty(total, dtype=float)
    window = np.hanning(size).astype(np.float32)
    for first in range(0, total, CHUNK_BLOCKS):
        blocks = min(CHUNK_BLOCKS, total - first)
        iq = recording.iq(first * size, blocks * size).reshape(blocks, size)
        spectrum = np.fft.fft(iq * window, axis=1)
        out[first:first + blocks] = np.sum(np.abs(spectrum[:, inside]) ** 2,
                                           axis=1)
    return out


def occupancy(recording: Recording, channel_hz: float, exchange_s: float,
              offset_hz: float = 0.0,
              threshold_db: float = DEFAULT_THRESHOLD_DB,
              block_s: float = BLOCK_S) -> Occupancy:
    """How often an exchange of ``exchange_s`` would meet other traffic."""
    power = channel_power(recording, channel_hz, offset_hz, block_s)
    size = max(int(round(block_s * recording.sample_rate_hz)), 16)
    block_s = size / recording.sample_rate_hz
    span = max(int(math.ceil(exchange_s / block_s)), 1)
    if len(power) < span:
        raise ValueError(
            "the recording is {:.3g} s long and one exchange {:.3g} s: record "
            "for longer".format(len(power) * block_s, exchange_s))
    quiet = float(np.percentile(power, QUIET_PERCENTILE))
    busy = power > quiet * 10.0 ** (threshold_db / 10.0)
    running = np.concatenate(([0], np.cumsum(busy)))
    touched = (running[span:] - running[:-span]) > 0
    return Occupancy(
        busy_share=float(busy.mean()),
        exchange_loss=float(touched.mean()),
        exchange_s=exchange_s,
        block_s=block_s,
        blocks=len(power),
        quiet_level=quiet,
        threshold_db=threshold_db,
        channel_hz=channel_hz,
        offset_hz=offset_hz,
        duration_s=len(power) * block_s,
    )


def packet_loss(path, key: str = "site.urban_packet_loss",
                threshold_db: float = DEFAULT_THRESHOLD_DB,
                offset_hz: float = 0.0):
    """A recording, as the `defaults.toml` entry it measures.

    The channel width and the exchange length are the model's own, for
    the SX1280 the urban and rural rows use, so the figure answers the
    question the default stands in for.
    """
    from yerkon.calibrate import Measured
    from yerkon.hardware import SX1280
    from yerkon.numbers import decimal_comma
    from yerkon.ranging import SINGLE_SIDED, exchange_duration_s
    from yerkon.settings import DEFAULTS

    recording = read_recording(path)
    exchange_s = exchange_duration_s(SX1280, SINGLE_SIDED)
    found = occupancy(recording, float(SX1280.ranging_bandwidth_hz.value),
                      exchange_s, offset_hz=offset_hz,
                      threshold_db=threshold_db)
    where = ("{} MHz".format(decimal_comma(recording.centre_hz / 1e6, 3))
             if recording.centre_hz else "merkez frekansı dosyada yok")
    try:
        was = DEFAULTS.number(key)
    except KeyError:
        was = None
    return Measured(
        key=key,
        value=round(found.exchange_loss, 4),
        unit="fraction",
        source="{} ({}, {} s kayıt)".format(
            recording.path.name, where, decimal_comma(found.duration_s, 1)),
        note=(
            "Kanal {} kHz, {} ms'lik alışverişler: blokların %{}'i dolu, "
            "alışverişlerin %{}'i başka bir yayına denk geliyor. Eşik sessiz "
            "seviyenin {} dB üstü.".format(
                decimal_comma(found.channel_hz / 1e3, 0),
                decimal_comma(found.exchange_s * 1e3, 1),
                decimal_comma(100.0 * found.busy_share, 1),
                decimal_comma(100.0 * found.exchange_loss, 1),
                decimal_comma(found.threshold_db, 1))),
        was=was,
    )
