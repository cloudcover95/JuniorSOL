#!/usr/bin/env python3
"""Local CU receipt. Packs a member note. No chain submit."""
import json, sys
from pathlib import Path

def pack_note(note: str) -> dict:
    xs = [float((ord(c) % 13) - 6) for c in (note or "x")]
    s = sum(abs(x) for x in xs) or 1.0
    g = s / len(xs) + 1e-7
    trit = []
    for x in xs:
        q = round(x / g)
        trit.append(1 if q > 1 else (-1 if q < -1 else int(q)))
    zeros = sum(1 for t in trit if t == 0) / max(1, len(trit))
    return {
        "app": "JuniorSOL",
        "note": note,
        "gamma": g,
        "sparsity": zeros,
        "chain_submit": False,
        "rpc": False,
        "credit_union": "local-ledger",
        "protocol": "goldend-osai-omega/1",
    }

print(json.dumps(pack_note(" ".join(sys.argv[1:]) or "member share"), indent=2))
