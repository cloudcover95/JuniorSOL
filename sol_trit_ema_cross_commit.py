"""JuniorSOL trit EMA-cross commit. Pure math: fast-vs-slow EMA spread trits per port, chained with side_commit.

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


def ema(series, span: int) -> list[float]:
    """Exponential moving average with alpha = 2 / (span + 1), seeded at the first value."""
    if span < 1:
        raise ValueError("span must be >= 1")
    a = 2.0 / (span + 1)
    out = []
    for i, x in enumerate(series):
        out.append(float(x) if i == 0 else a * x + (1 - a) * out[-1])
    return out


def ema_cross_trits(series, fast: int = 3, slow: int = 8, band: float = RATE) -> list[int]:
    """Trit per step: +1 if (fast - slow) / |slow| > band, -1 if < -band, else 0.

    A zero slow EMA gives 0.
    """
    if fast >= slow:
        raise ValueError("fast span must be shorter than slow span")
    f, s = ema(series, fast), ema(series, slow)
    out = []
    for fv, sv in zip(f, s):
        if sv == 0:
            out.append(0)
            continue
        d = (fv - sv) / abs(sv)
        out.append(1 if d > band else (-1 if d < -band else 0))
    return out


def port_chain(port_series: dict, fast: int = 3, slow: int = 8, prev: str = "0" * 16) -> dict:
    """Commit each port's EMA-cross trits in PORTS order; each commit chains from the last."""
    result = {}
    for port in PORTS:
        if port not in port_series:
            continue
        t = ema_cross_trits(port_series[port], fast, slow)
        pk = pack(t)
        prev = side_commit(prev, pk, port)
        result[port] = {"trits": t, "pack": pk.hex(), "commit": prev}
    return {"ports": result, "close": prev}


if __name__ == "__main__":
    assert ema([10, 10, 10], 3) == [10.0, 10.0, 10.0]
    assert ema_cross_trits([100] * 6) == [0] * 6
    up = ema_cross_trits([100, 110, 125, 145, 170, 200])
    dn = ema_cross_trits([200, 170, 145, 125, 110, 100])
    assert up[0] == 0 and up[-1] == 1 and dn[0] == 0 and dn[-1] == -1
    assert ema_cross_trits([0, 0, 0]) == [0, 0, 0]
    assert pack([1, 0, -1, -1, 1, 0, 1]).hex() == "4a44"
    series = {p: [100 + k * (i - 2) * 6 for k in range(10)] for i, p in enumerate(PORTS)}
    a = port_chain(series)
    assert a == port_chain(series) and len(a["close"]) == 16
    assert list(a["ports"]) == list(PORTS)
    assert not (MINT or SOCKET or LAYER_ONE) and RATE == 0.05
    print({"close": a["close"], "ok": True})
