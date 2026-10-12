#!/bin/sh
# Run from this folder after `conda env create -f environment.yml && conda activate interaction-ratio-redistricting`.
# Extra arguments are passed to run_chains.py, e.g. ./run.sh --steps 100 --seeds 2018
set -e
export FLOWS_MATRIX_PATH="${FLOWS_MATRIX_PATH:-data/synthetic_flows.npy}"
[ -f "$FLOWS_MATRIX_PATH" ] || python make_synthetic_flows.py
python run_chains.py "$@"
python summarize.py output
