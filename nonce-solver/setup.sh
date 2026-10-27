#!/bin/bash
set -e
sudo apt-get update -qq && sudo apt-get install -y -qq build-essential git >/dev/null
cat data/sample.gz.part* | gunzip > data/sample_balanced_1536.cnf
pip install -q numpy python-sat
[ -d kissat ] || git clone -q --depth 1 https://github.com/arminbiere/kissat.git
cd kissat && ./configure -O3 >/dev/null && make -j"$(nproc)" >/dev/null && cd ..
echo "kissat built: $(./kissat/build/kissat --version)"
