"""JuniorSOL trit z-score commit. Pure math: rolling z-score band trits per port, chained with side_commit.

Ports: Home, OSai, FieldCore, Flagstaff, JuniorLLM. Hex is a receipt, not an account.
Pack and close rule match sol_trit_side (i2s 2-bit, 0->0, 1->1, -1->2; sha256(prev || pack || text)[:16]).
"""
from __future__ import annotations

import hashlib
import math

RATE = 0.05
MINT = False
SOCKET = False
LAYER_ONE = False

PORTS = ("Home", "OSai", "FieldCore", "Flagstaff", "JuniorLLM")

_ENC = {0: 0, 1: 1, -1: 2}


def pack(trits) -> bytes:
    """Balanced trits as 2-bit i2s codes, MSB first, zero-padded (same layout as sol_trit_side)."""
    acc = bits = 0
    out = bytearray()
    for t in trits:
        if t not in _ENC:
            raise ValueError("trit must be -1, 0 or 1")
        acc = (acc << 2) | _ENC[t]
        bits += 2
        if bits == 8:
            out.append(acc)
            acc = bits = 0
    if bits:
        out.append(acc << (8 - bits))
    return bytes(out)


def side_commit(prev: str, pk: bytes, text: str) -> str:
    """sha256(prev || pack || text)[:16]."""
    return hashlib.sha256(prev.encode() + pk + text.encode()).hexdigest()[:16]


def rolling_z(series, window: int = 5) -> list[float]:
    """Z-score of each value against the trailing window (inclusive). Zero spread or short history gives 0."""
    if window < 2:
        raise ValueError("window must be >= 2")
    xs = [float(x) for x in series]
    out = []
    for i, x in enumerate(xs):
        w = xs[max(0, i - window + 1): i + 1]
        if len(w) < 2:
            out.append(0.0)
            continue
        m = sum(w) / len(w)
        sd = math.sqrt(sum((v - m) ** 2 for v in w) / len(w))
        out.append(0.0 if sd == 0 else (x - m) / sd)
    return out


def zscore_trits(series, window: int = 5, z: float = 1.0) -> list[int]:
    """Trit per step: +1 if z-score > z, -1 if < -z, else 0."""
    if z <= 0:
        raise ValueError("z must be > 0")
    return [1 if v > z else (-1 if v < -z else 0) for v in rolling_z(series, window)]


def port_chain(port_series: dict, window: int = 5, z: float = 1.0, prev: str = "0" * 16) -> dict:
    """Commit each port's z-score trits in PORTS order; each commit chains from the last."""
    result = {}
    for port in PORTS:
        if port not in port_series:
            continue
        t = zscore_trits(port_series[port], window, z)
        pk = pack(t)
        prev = side_commit(prev, pk, port)
        result[port] = {"trits": t, "pack": pk.hex(), "commit": prev}
    return {"ports": result, "close": prev}


if __name__ == "__main__":
    assert rolling_z([5, 5, 5, 5]) == [0.0] * 4
    assert zscore_trits([100] * 6) == [0] * 6
    assert zscore_trits([100, 100, 100, 100, 130]) == [0, 0, 0, 0, 1]
    assert zscore_trits([100, 100, 100, 100, 70]) == [0, 0, 0, 0, -1]
    assert zscore_trits([1, 2]) == [0, 0]
    assert pack([1, 0, -1, -1, 1, 0, 1]).hex() == "4a44"
    series = {p: [100 + ((k * (i + 3)) % 7) * 4 for k in range(10)] for i, p in enumerate(PORTS)}
    a = port_chain(series)
    assert a == port_chain(series) and len(a["close"]) == 16
    assert list(a["ports"]) == list(PORTS)
    assert not (MINT or SOCKET or LAYER_ONE) and RATE == 0.05
    print({"close": a["close"], "ok": True})
