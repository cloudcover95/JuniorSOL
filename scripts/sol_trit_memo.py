#!/usr/bin/env python3
import json, sys

def i2s_hex(trits):
    acc = bits = 0
    out = []
    for t in trits:
        c = 0 if t == 0 else (1 if t == 1 else 2)
        acc = (acc << 2) | c
        bits += 2
        if bits == 8:
            out.append(acc)
            acc = bits = 0
    if bits:
        out.append(acc << (8 - bits))
    return bytes(out).hex()

def memo(note: str) -> dict:
    xs = [float((ord(c) % 13) - 6) for c in (note or "x")]
    g = sum(abs(x) for x in xs) / len(xs) + 1e-7
    trit = []
    for x in xs:
        q = round(x / g)
        trit.append(1 if q > 1 else (-1 if q < -1 else int(q)))
    hx = i2s_hex(trit)
    return {"memo_hex": hx, "n": len(trit), "gamma": g, "program": False, "rpc": False, "cu": "local"}

print(json.dumps(memo(" ".join(sys.argv[1:]) or "member share"), indent=2))
