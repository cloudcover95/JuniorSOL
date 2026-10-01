"""JuniorSOL surface compute. Hex is a receipt, not an account."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

MESH = Path.home() / ".juniorhome" / "gaia_mesh" / "sol_surface.jsonl"


def compute(note: str = "sol") -> dict:
    digest = hashlib.sha3_256(note.encode()).hexdigest()[:16]
    body = {
        "protocol": "goldend-osai-omega/1",
        "port": "JuniorSOL",
        "receipt": digest,
        "address": False,
        "rpc": False,
        "model_pull": False,
        "bind": "127.0.0.1",
    }
    MESH.parent.mkdir(parents=True, exist_ok=True)
    with MESH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(body) + "\n")
    return body


if __name__ == "__main__":
    print(json.dumps(compute(), indent=2))
