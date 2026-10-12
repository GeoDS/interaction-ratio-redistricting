#!/bin/sh
# Run from this folder after `conda env create -f environment.yml && conda activate redis2`.
set -e
export PYTHONPATH="$PWD/gerrychain_modified"
export FLOWS_MATRIX_PATH="${FLOWS_MATRIX_PATH:-data/synthetic_flows.npy}"

[ -f "$FLOWS_MATRIX_PATH" ] || python make_synthetic_flows.py

python run_chains.py \
    --geojson_file_path=data/wi_2020_cbgs_voting_demo.geojson \
    --matrix_index_geoid_dict=data/cbg_indices_WI_houseDis_pmc_2020.json \
    --recomb_type=recom --election=HOUSE18 --state=wi --year=2020

python interaction_ratio_parallel.py
