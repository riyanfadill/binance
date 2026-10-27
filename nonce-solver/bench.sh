#!/bin/bash
# Portfolio: one kissat per core with different seeds/configs; first SAT wins.
CNF=${1:-data/sample_balanced_1536.cnf}; T=${2:-840}; N=$(nproc); K=./kissat/build/kissat
mkdir -p out; rm -f out/*; start=$(date +%s)
for i in $(seq 0 $((N-1))); do
  case $((i%3)) in 0) cfg="--sat";; 1) cfg="--target=2";; 2) cfg="";; esac
  ( timeout $T $K -q $cfg --seed=$i "$CNF" > out/k$i.txt; ) &
done
while true; do
  w=$(grep -l "^s SATISFIABLE" out/*.txt 2>/dev/null | head -1)
  if [ -n "$w" ]; then echo "SOLVED by $w in $(( $(date +%s)-start ))s"; pkill -f kissat/build/kissat; break; fi
  [ $(jobs -r | wc -l) -eq 0 ] && { echo "no solution within ${T}s"; break; }
  sleep 1
done
