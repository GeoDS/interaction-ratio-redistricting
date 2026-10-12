# Methods code

> **Methodology, not replication.** This folder contains a working implementation of the paper's approach: ReCom ensembles with a flow-biased spanning tree, scored by interaction ratio, compactness, and efficiency gap. It is an earlier (November 2022) version of the code, and its settings differ from those used for the published results (see below). It also runs on **synthetic** mobility flows, because the original SafeGraph data cannot be redistributed. Use it to understand, adapt, or extend the method. It will **not** reproduce the paper's figures or numbers.

## What's here

| Path | Contents |
|---|---|
| `run_chains.py` | Builds the CBG adjacency graph, weights edges by mobility flows, runs ReCom chains in parallel, and saves per-plan compactness, efficiency gap, and district assignments |
| `interaction_ratio_parallel.py` | Computes the interaction ratio for every plan in a chain from its assignments and the flow matrix |
| `interaction_ratio_serial.py` | Serial IR helpers, including incremental updates when only a few CBGs change district |
| `gerrychain_modified/` | GerryChain 0.2.20 with a modified `tree.py` (see below) |
| `make_synthetic_flows.py` | Generates the stand-in flow matrix |
| `seed_comparison.ipynb` | Exploratory analysis of chain parameters and seeds |
| `run.sh` | Runs the full pipeline |
| `environment.yml` | Conda environment used at the time (Python 3.10) |
| `data/` | Wisconsin CBG geometry with 2020 census demographics and 2018–2020 election returns, plus the CBG-to-matrix-row index |
| `results_1000step/` | Chain outputs from the original runs on the real flows |

## How the biased spanning tree works here

`gerrychain_modified/gerrychain/tree.py` replaces `random_spanning_tree` with a `bias` parameter:

- `bias = -99`: standard ReCom. Random edge weights, then a maximum spanning tree.
- any other `bias`: a random-walk (Wilson-style) spanning tree. Each step moves to a neighbouring CBG with probability proportional to `flow ** bias`. With `bias = 1`, CBGs with strong mobility ties are more likely to be joined in the tree, and so more likely to land in the same district.

## How this differs from the published experiments

| | This code | Paper |
|---|---|---|
| Chain length | 1,000 steps | 10,000 steps |
| Compactness bounds | 1×, 3×, 5× cut edges | 1×, 5× |
| Population tolerance | 1% (constraint), 2% (ReCom ε) | up to 3% |
| Biasing | `flow ** bias` random walk (`bias` = 1) | random weight × flow × bias factor (±100), then maximum spanning tree |
| Max-/min-IR cut | not included | included |
| Seeds | 2018, 1776, 1993 | — |
| Flows | synthetic (see below) | SafeGraph 2020 |

## Data

**Included:** `data/wi_2020_cbgs_voting_demo.geojson` holds 4,678 Wisconsin census block groups with population and demographics (2020 PL 94-171, via the Redistricting Data Hub) and ward-level election returns disaggregated to CBGs. It also includes the seed plan's district assignment (`dis_id`), from the People's Maps Commission.

**Not included: the mobility flows.** The paper uses SafeGraph Neighborhood Patterns, whose license does not allow redistribution, even in derived form. Instead, `make_synthetic_flows.py` writes `data/synthetic_flows.npy`, a 4,678 × 4,678 matrix with the same shape, row order, and units:

- flows follow a noisy gravity model: proportional to destination population, divided by (distance + 1 km)², times log-normal noise
- each row is scaled to 10 trips per resident

It exists so the code runs end to end. Interaction ratios computed on it are **not** meaningful.

**Using real flows:** build a matrix in the row order of `cbg_indices_WI_houseDis_pmc_2020.json`, where `flows[o, d]` is the trips from CBG `o` to CBG `d`, then point `FLOWS_MATRIX_PATH` at it. In the paper, SafeGraph device counts were scaled to population as `device_flows(o,d) × pop(o) / devices(o)` and averaged over the months of 2020. Public, already-scaled flows from the same source are available at the census-tract level in [GeoDS/COVID19USFlows](https://github.com/GeoDS/COVID19USFlows).

## Running

```sh
conda env create -f environment.yml
conda activate redis2
./run.sh        # generates synthetic flows if missing, then runs chains + IR into output/
```

Chain settings (biases, seeds, compactness bounds, steps) are the lists at the bottom of `run_chains.py` and `interaction_ratio_parallel.py`. Keep them in sync. The full default grid is 18 chains of 1,000 steps and is meant for a many-core machine.

Outputs are named `{date}_{steps}it_{compactness}comp_{bias}bias_{seed}seed_wi_2020`:

| Suffix | Contents |
|---|---|
| `.csv` | mean Polsby–Popper compactness and efficiency gap for each plan |
| `_assignments.csv` | the district of every CBG in every plan |
| `_interaction_ratios.csv` | the above, plus interaction ratio |

## Credits

Developed by Jacob Kruse as a CS 744 (UW–Madison) course project. It builds on [GerryChain](https://github.com/mggg/gerrychain) by the MGGG Redistricting Lab.
