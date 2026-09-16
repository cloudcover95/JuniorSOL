# Trit logic vs Solana

SVM does not have a ternary opcode. JuniorSOL uses 1.58 as a **memo / receipt**:

1. Member note → AbsMean or Winsor → {-1,0,1}
2. Pack 2 bits/trit (0→0, 1→1, -1→2) → hex
3. That hex is a local commitment. It is not a program id and not a signature.

On-chain, if you ever submit, it would be a memo or a 32-byte hash of the hex — still operator RPC, not Home automation.

Credit-union share here = jsonl + trit hex. No mint.
