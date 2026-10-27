# nonce-solver
Benchmark for NONCE nonce-logic-balanced-1536 (5-SAT, 1536 vars, 33,792 clauses).
1. Code > Codespaces > ... > New with options: branch `nonce-solver`, dev container `nonce-solver`, biggest machine type.
2. Setup builds kissat automatically. If not: `bash setup.sh`.
3. `bash bench.sh` runs a kissat portfolio on every core against the saved instance (840 s limit) and prints the solve time.
