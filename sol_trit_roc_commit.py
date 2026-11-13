"""JuniorSOL trit rate-of-change commit. Pure math: ROC band trits per port, chained with side_commit.

Ports: Home, OSai, FieldCore, Flagstaff, JuniorLLM. Hex is a receipt, not an account.
Pack and close rule match sol_trit_side (i2s 2-bit, 0->0, 1->1, -1->2; sha256(prev || pack || text)[:16]).
"""
from __future__ import annotations

import hashlib

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


def roc(series, period: int = 3) -> list[float]:
    """Rate of change (x[i] - x[i-period]) / |x[i-period]|; 0.0 for warm-up or a zero base."""
    if period < 1:
        raise ValueError("period must be >= 1")
    out = []
    for i, x in enumerate(series):
        if i < period or series[i - period] == 0:
            out.append(0.0)
        else:
            base = series[i - period]
            out.append((x - base) / abs(base))
    return out


def roc_trits(series, period: int = 3, band: float = RATE) -> list[int]:
    """Trit per step: +1 if ROC > band, -1 if ROC < -band, else 0."""
    return [1 if r > band else (-1 if r < -band else 0) for r in roc(series, period)]


def port_chain(port_series: dict, period: int = 3, prev: str = "0" * 16) -> dict:
    """Commit each port's ROC trits in PORTS order; each commit chains from the last."""
    result = {}
    for port in PORTS:
        if port not in port_series:
            continue
        t = roc_trits(port_series[port], period)
        pk = pack(t)
        prev = side_commit(prev, pk, port)
        result[port] = {"trits": t, "pack": pk.hex(), "commit": prev}
    return {"ports": result, "close": prev}


if __name__ == "__main__":
    assert roc([100, 100, 100, 110], 3) == [0.0, 0.0, 0.0, 0.1]
    assert roc_trits([100] * 6) == [0] * 6
    assert roc_trits([100, 101, 102, 110, 120, 130]) == [0, 0, 0, 1, 1, 1]
    assert roc_trits([130, 120, 110, 100, 90, 80]) == [0, 0, 0, -1, -1, -1]
    assert roc_trits([0, 0, 0, 5]) == [0, 0, 0, 0]
    assert pack([1, 0, -1, -1, 1, 0, 1]).hex() == "4a44"
    series = {p: [100 + k * (i - 2) * 6 for k in range(10)] for i, p in enumerate(PORTS)}
    a = port_chain(series)
    assert a == port_chain(series) and len(a["close"]) == 16
    assert list(a["ports"]) == list(PORTS)
    assert not (MINT or SOCKET or LAYER_ONE) and RATE == 0.05
    print({"close": a["close"], "ok": True})
