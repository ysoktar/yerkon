"""Band recordings from SDR++ and SDRangel, as packet loss (ADR-0083)."""

import struct
import wave
import zlib

import numpy as np
import pytest

from yerkon.spectrum import (
    BLOCK_S,
    SDRIQ_HEADER,
    occupancy,
    packet_loss,
    read_recording,
)

RATE = 4_000_000.0
CHANNEL = 1_625_000.0


def _bursty(seconds, period_s, burst_s, seed=1, burst_offset_hz=0.0):
    """Noise, with a strong in-channel burst every ``period_s``."""
    rng = np.random.default_rng(seed)
    n = int(seconds * RATE)
    iq = (rng.normal(0, 0.01, n) + 1j * rng.normal(0, 0.01, n)).astype(np.complex64)
    t = np.arange(n) / RATE
    on = (t % period_s) < burst_s
    tone = 0.2 * np.exp(2j * np.pi * (burst_offset_hz + 200e3) * t)
    iq[on] += tone[on].astype(np.complex64)
    return iq


def _write_sdrpp(path, iq, kind="int16"):
    scale = {"int16": 32767.0, "uint8": 127.0}[kind]
    interleaved = np.empty(2 * len(iq), dtype=np.float32)
    interleaved[0::2], interleaved[1::2] = iq.real, iq.imag
    if kind == "int16":
        data = np.clip(interleaved * scale, -32768, 32767).astype("<i2").tobytes()
        width = 2
    else:
        data = np.clip(interleaved * scale + 128.0, 0, 255).astype(np.uint8).tobytes()
        width = 1
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(width)
        out.setframerate(int(RATE))
        out.writeframes(data)


def _write_sdrangel(path, iq, centre_hz=2_440_000_000, bits=16, damage=False):
    head = SDRIQ_HEADER.pack(int(RATE), centre_hz, 0, bits, 0, 0)[:28]
    crc = zlib.crc32(head) & 0xFFFFFFFF
    if damage:
        crc ^= 1
    kind, scale = ("<i2", 32767.0) if bits == 16 else ("<i4", 8388607.0)
    interleaved = np.empty(2 * len(iq), dtype=np.float64)
    interleaved[0::2], interleaved[1::2] = iq.real, iq.imag
    path.write_bytes(head + struct.pack("<I", crc)
                     + (interleaved * scale).astype(kind).tobytes())


def _expected(period_s, burst_s, exchange_s, seconds):
    """Exchange windows that touch a burst, counted directly on blocks."""
    blocks = int(seconds / BLOCK_S)
    t = (np.arange(blocks) * BLOCK_S)
    # A block is busy when any part of it overlaps a burst.
    start = t % period_s
    busy = (start < burst_s) | (start + BLOCK_S > period_s)
    span = int(np.ceil(exchange_s / BLOCK_S))
    running = np.concatenate(([0], np.cumsum(busy)))
    return float(((running[span:] - running[:-span]) > 0).mean())


def test_a_quiet_channel_loses_nothing(tmp_path):
    path = tmp_path / "quiet_2440000000Hz.wav"
    _write_sdrpp(path, _bursty(1.0, 1.0, 0.0))
    found = occupancy(read_recording(path), CHANNEL, 0.0318)
    assert found.busy_share < 0.01
    assert found.exchange_loss < 0.02


def test_bursts_cost_the_exchanges_that_overlap_them(tmp_path):
    """Two millisecond bursts every twenty: a 31,8 ms exchange always
    meets one, though only a tenth of the air is taken."""
    path = tmp_path / "busy.wav"
    _write_sdrpp(path, _bursty(2.0, 0.020, 0.002))
    found = occupancy(read_recording(path), CHANNEL, 0.0318)
    assert found.busy_share == pytest.approx(0.1, abs=0.04)
    assert found.exchange_loss == pytest.approx(1.0)


def test_the_loss_is_the_share_of_windows_that_touch_a_burst(tmp_path):
    path = tmp_path / "sparse.wav"
    _write_sdrpp(path, _bursty(4.0, 0.200, 0.010))
    found = occupancy(read_recording(path), CHANNEL, 0.0318)
    assert found.exchange_loss == pytest.approx(
        _expected(0.200, 0.010, 0.0318, 4.0), abs=0.02)


def test_traffic_outside_the_channel_does_not_count(tmp_path):
    """A neighbour 1,5 MHz away is filtered out by the anchor's receiver."""
    path = tmp_path / "neighbour.wav"
    _write_sdrpp(path, _bursty(2.0, 0.020, 0.010, burst_offset_hz=1_300_000.0))
    found = occupancy(read_recording(path), CHANNEL, 0.0318)
    assert found.exchange_loss < 0.05


def test_both_recorders_give_the_same_answer_for_the_same_air(tmp_path):
    iq = _bursty(3.0, 0.150, 0.012)
    wav, sdriq = tmp_path / "a_2440000000Hz.wav", tmp_path / "a.sdriq"
    _write_sdrpp(wav, iq)
    _write_sdrangel(sdriq, iq)
    one = occupancy(read_recording(wav), CHANNEL, 0.0318)
    other = occupancy(read_recording(sdriq), CHANNEL, 0.0318)
    assert one.exchange_loss == pytest.approx(other.exchange_loss, abs=0.01)
    assert read_recording(sdriq).centre_hz == 2_440_000_000
    assert read_recording(wav).centre_hz == 2_440_000_000


def test_sdrpp_eight_bit_and_sdrangel_24_bit_are_read(tmp_path):
    iq = _bursty(2.0, 0.150, 0.012)
    eight, wide = tmp_path / "b.wav", tmp_path / "b.sdriq"
    _write_sdrpp(eight, iq, kind="uint8")
    _write_sdrangel(wide, iq, bits=24)
    reference = _expected(0.150, 0.012, 0.0318, 2.0)
    for path in (eight, wide):
        found = occupancy(read_recording(path), CHANNEL, 0.0318)
        assert found.exchange_loss == pytest.approx(reference, abs=0.03), path


def test_a_damaged_header_is_refused_rather_than_read(tmp_path):
    path = tmp_path / "c.sdriq"
    _write_sdrangel(path, _bursty(0.2, 1.0, 0.0), damage=True)
    with pytest.raises(ValueError, match="checksum"):
        read_recording(path)


def test_an_audio_recording_is_refused(tmp_path):
    path = tmp_path / "audio.wav"
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(48000)
        out.writeframes(b"\x00\x00" * 4800)
    with pytest.raises(ValueError, match="two, I and Q"):
        read_recording(path)


def test_a_recording_narrower_than_the_channel_is_refused(tmp_path):
    path = tmp_path / "narrow.wav"
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(1_000_000)
        out.writeframes(b"\x00\x00\x00\x00" * 100_000)
    with pytest.raises(ValueError, match="at least as wide as the channel"):
        occupancy(read_recording(path), CHANNEL, 0.0318)


def test_calibrate_turns_a_recording_into_the_default_it_replaces(tmp_path):
    """The loop the MATLAB readers close, for the figure nothing measured."""
    from yerkon.calibrate import read

    path = tmp_path / "site_2440000000Hz.wav"
    _write_sdrpp(path, _bursty(3.0, 0.150, 0.012))
    measured = read(str(path))
    assert measured.key == "site.urban_packet_loss"
    assert measured.was == pytest.approx(0.15)
    assert 0.0 < measured.value < 1.0
    toml = measured.as_toml()
    assert 'provenance = "MEASUREMENT"' in toml
    assert "2440" in measured.source

    rural = packet_loss(path, key="ranging.packet_loss")
    assert rural.key == "ranging.packet_loss"


def test_the_command_prints_the_entry(tmp_path, capsys):
    from yerkon.cli import calibrate

    path = tmp_path / "site.sdriq"
    _write_sdrangel(path, _bursty(2.0, 0.150, 0.012))
    assert calibrate([str(path), "--threshold-db", "6"]) == 0
    printed = capsys.readouterr().out
    assert '[values."site.urban_packet_loss"]' in printed
    assert "6,0 dB" in printed
