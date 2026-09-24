"""The PNG reader a plain install fetches ground with (ADR-0087)."""

import io

import numpy as np
import pytest

from yerkon.site import png

PIL = pytest.importorskip("PIL.Image")


def _picture():
    rng = np.random.default_rng(7)
    # Smooth ramps as well as noise, so an encoder picks every filter.
    ramp = np.linspace(0, 255, 64, dtype=np.uint8)
    smooth = np.stack(np.broadcast_arrays(ramp[None, :], ramp[:, None],
                                          ramp[None, :] // 2), axis=-1)
    noisy = rng.integers(0, 256, (64, 64, 3)).astype(np.uint8)
    return np.concatenate([smooth, noisy], axis=0)


@pytest.mark.parametrize("mode", ["RGB", "RGBA", "L", "LA", "P"])
def test_it_reads_what_pillow_writes(mode):
    picture = PIL.fromarray(_picture()).convert(mode)
    buffer = io.BytesIO()
    picture.save(buffer, "PNG", optimize=True)
    expected = np.asarray(picture.convert("RGB"))
    assert np.array_equal(png.read_rgb(buffer.getvalue()), expected)


def test_what_it_writes_pillow_reads_and_it_reads_back():
    pixels = _picture()
    written = png.write_rgb(pixels)
    assert np.array_equal(np.asarray(PIL.open(io.BytesIO(written))), pixels)
    assert np.array_equal(png.read_rgb(written), pixels)


def test_what_it_cannot_read_it_refuses_with_a_reason():
    with pytest.raises(png.NotReadable):
        png.read_rgb(b"not a picture")
    import struct

    header = struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 1)
    interlaced = png.SIGNATURE + png._chunk(b"IHDR", header) + png._chunk(
        b"IEND", b"")
    with pytest.raises(png.NotReadable, match="interlaced"):
        png.read_rgb(interlaced)
    sixteen = png.SIGNATURE + png._chunk(
        b"IHDR", struct.pack(">IIBBBBB", 4, 4, 16, 2, 0, 0, 0))
    with pytest.raises(png.NotReadable, match="16-bit"):
        png.read_rgb(sixteen)
