"""Reading and writing PNG with numpy and zlib alone (ADR-0087).

Terrain tiles arrive as PNG, and a plain install has numpy and nothing
else: no Pillow. A PNG is a zlib stream of rows, each behind a filter
byte, and the five filters are a few lines each. Pillow is used where it
is installed because it is faster; this is what runs where it is not.

Eight bits a sample, not interlaced: every tile server this project
reads writes that, and anything else is refused with a sentence rather
than read wrongly.
"""

from __future__ import annotations

import struct
import zlib

import numpy as np

SIGNATURE = b"\x89PNG\r\n\x1a\n"

#: Samples a pixel holds, by PNG colour type.
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


class NotReadable(ValueError):
    """A PNG this reader does not handle."""


def read_rgb(data: bytes) -> np.ndarray:
    """The picture as an (height, width, 3) array of uint8."""
    width, height, depth, colour, interlace, chunks = _chunks(data)
    if depth != 8:
        raise NotReadable("{}-bit samples; only 8-bit is read".format(depth))
    if interlace:
        raise NotReadable("interlaced PNG is not read")
    if colour not in CHANNELS:
        raise NotReadable("colour type {} is not PNG".format(colour))

    per_pixel = CHANNELS[colour]
    raw = zlib.decompress(b"".join(body for kind, body in chunks
                                   if kind == b"IDAT"))
    samples = _unfiltered(raw, width, height, per_pixel)

    if colour == 3:
        palette = next((body for kind, body in chunks if kind == b"PLTE"), None)
        if palette is None:
            raise NotReadable("a palette image with no palette")
        table = np.frombuffer(palette, dtype=np.uint8).reshape(-1, 3)
        return table[samples[..., 0]]
    if colour in (0, 4):
        return np.repeat(samples[..., :1], 3, axis=2)
    return samples[..., :3].copy()


def write_rgb(pixels: np.ndarray) -> bytes:
    """An (height, width, 3) uint8 array as PNG bytes, unfiltered."""
    pixels = np.ascontiguousarray(pixels, dtype=np.uint8)
    height, width, _ = pixels.shape
    rows = np.concatenate(
        [np.zeros((height, 1), dtype=np.uint8), pixels.reshape(height, -1)],
        axis=1)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (SIGNATURE + _chunk(b"IHDR", header)
            + _chunk(b"IDAT", zlib.compress(rows.tobytes(), 6))
            + _chunk(b"IEND", b""))


def _chunk(kind: bytes, body: bytes) -> bytes:
    return (struct.pack(">I", len(body)) + kind + body
            + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))


def _chunks(data: bytes):
    if not data.startswith(SIGNATURE):
        raise NotReadable("not a PNG")
    at = len(SIGNATURE)
    chunks = []
    header = None
    while at + 8 <= len(data):
        length, = struct.unpack(">I", data[at:at + 4])
        kind = data[at + 4:at + 8]
        body = data[at + 8:at + 8 + length]
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        chunks.append((kind, body))
        at += 12 + length
        if kind == b"IEND":
            break
    if header is None:
        raise NotReadable("a PNG with no header")
    width, height, depth, colour, _, _, interlace = header
    return width, height, depth, colour, interlace, chunks


def _unfiltered(raw: bytes, width: int, height: int, per_pixel: int) -> np.ndarray:
    """Undo each row's filter. Sub and Up are whole-row array sums;
    Average and Paeth depend on the byte to their left and run as a loop
    over plain integers, which is quicker than numpy one byte at a time."""
    stride = width * per_pixel
    out = np.zeros((height, stride), dtype=np.uint8)
    previous = np.zeros(stride, dtype=np.int64)
    view = memoryview(raw)
    for row in range(height):
        start = row * (stride + 1)
        kind = raw[start]
        line = np.frombuffer(view[start + 1:start + 1 + stride], dtype=np.uint8)
        if kind == 0:
            current = line.astype(np.int64)
        elif kind == 1:
            current = (np.cumsum(line.reshape(-1, per_pixel).astype(np.int64),
                                 axis=0) % 256).reshape(-1)
        elif kind == 2:
            current = (line.astype(np.int64) + previous) % 256
        elif kind in (3, 4):
            current = np.array(_sequential(kind, line.tolist(),
                                           previous.tolist(), per_pixel),
                               dtype=np.int64)
        else:
            raise NotReadable("filter {} is not PNG".format(kind))
        out[row] = current
        previous = current
    return out.reshape(height, width, per_pixel)


def _sequential(kind: int, line: list, above: list, per_pixel: int) -> list:
    done = [0] * len(line)
    for i, value in enumerate(line):
        left = done[i - per_pixel] if i >= per_pixel else 0
        up = above[i]
        if kind == 3:
            done[i] = (value + ((left + up) >> 1)) & 0xFF
            continue
        corner = above[i - per_pixel] if i >= per_pixel else 0
        guess = left + up - corner
        to_left, to_up, to_corner = (abs(guess - left), abs(guess - up),
                                     abs(guess - corner))
        if to_left <= to_up and to_left <= to_corner:
            nearest = left
        elif to_up <= to_corner:
            nearest = up
        else:
            nearest = corner
        done[i] = (value + nearest) & 0xFF
    return done
