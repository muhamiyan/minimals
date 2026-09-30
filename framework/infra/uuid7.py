"""UUIDv7 generation.

UUIDv7 is a time-ordered UUID: 48 bits of Unix epoch milliseconds, then a
version nibble (7), then a variant + 74 bits of randomness. Time-ordering
makes it friendly as a primary key (roughly insertion-ordered, unlike v4).

Python's ``uuid`` module gains ``uuid7()`` only in 3.14, so this shared
helper provides it for the current runtime.
"""
from __future__ import annotations

import os
import time


def _as_hex(b: bytes) -> str:
    h = b.hex()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def uuid7() -> str:
    """Return a UUIDv7 string (lowercase, hyphenated).

    Layout (RFC 9562):
      bits 0-47   unix_ts_ms (48 bits, big-endian)
      bits 48-51  version = 7
      bits 52-63  rand_a (12 bits)
      bits 64-65  variant = 0b10
      bits 66-127 rand_b (62 bits)
    """
    ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF  # 12 bits
    rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)  # 62 bits

    b = bytearray(16)
    b[0:6] = ms.to_bytes(6, "big")
    b[6] = 0x70 | (rand_a >> 8)          # version 7 + high 4 bits of rand_a
    b[7] = rand_a & 0xFF                 # low 8 bits of rand_a
    b[8] = 0x80 | ((rand_b >> 56) & 0x3F)  # variant 10 + high 6 bits of rand_b
    b[9:16] = (rand_b & ((1 << 56) - 1)).to_bytes(7, "big")  # remaining 56 bits

    return _as_hex(bytes(b))


__all__ = ["uuid7"]
