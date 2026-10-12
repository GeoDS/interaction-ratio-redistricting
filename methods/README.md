# Methods code

> **Methodology, not replication.** This folder implements the paper's approach: ReCom ensembles with a flow-biased spanning tree, scored by interaction ratio, compactness, and efficiency gap. It comes from an earlier (November 2022) version of the experiments, and its settings differ from those used for the published results (see below). It also runs on **synthetic** mobility flows, because the original SafeGraph data cannot be redistributed. Use it to understand, adapt, or extend the method. It will **not** reproduce the paper's figures or numbers.

## What's here

| Path | Contents |
|---|---|
| [`run_chains.py`](run_chains.py) | Builds the CBG adjacency graph, weights edges by mobility flows, runs ReCom chains in parallel, and scores every plan |
| [`biased_tree.py`](biased_tree.py) | The flow-biased spanning tree: the only change made to [GerryChain](https://github.com/mggg/gerrychain) 0.2.20. Its docstring maps each change in the original modified copy of GerryChain to its new location |
| [`interaction_ratio.py`](interaction_ratio.py) | The interaction ratio for one plan |
| [`summarize.py`](summarize.py) | Writes `summary.csv` (IR range, median compactness and efficiency gap per chain) for a results folder |
| [`make_synthetic_flows.py`](make_synthetic_flows.py) | Generates the stand-in flow matrix |
| [`run.sh`](run.sh) | Runs the full pipeline |
| [`environment.yml`](environment.yml) | Conda environment (Python 3.10, GerryChain 0.2.20) |
| [`data/`](data/) | Wisconsin CBG geometry with 2020 census demographics and 2018–2020 election returns, plus the CBG-to-matrix-row index |
| [`results/`](results/) | Chain outputs from the original runs on the real flows |

## The biased spanning tree

ReCom repeatedly merges two adjacent districts, draws a spanning tree over their CBGs, and cuts one tree edge to split them into two population-balanced districts. `flow_biased_spanning_tree(graph, bias)` changes how that tree is drawn:

- `bias = -99`: standard ReCom (GerryChain's own random spanning tree).
- any other `bias`: a loop-erased random walk (Wilson's algorithm) in which each step moves to a neighbouring CBG with probability proportional to `flow ** bias`. With `bias = 1`, CBGs with strong mobility ties tend to stay connected in the tree, and so tend to land in the same district.

Given the same random seeds, it produces exactly the same trees as the original modified GerryChain.

## How this differs from the published experiments

| | This code | Paper |
|---|---|---|
| Chain length | 1,000 steps | 10,000 steps |
| Compactness bounds | 1×, 3×, 5× cut edges | 1×, 5× |
| Population tolerance | 1% (constraint), 2% (ReCom ε) | up to 3% |
| Biasing | `flow ** bias` random walk (`bias` = 1) | random weight × flow × bias factor (±100), then maximum spanning tree |
| Max-/min-IR cut | not included | included |
| Flows | synthetic (see below) | SafeGraph 2020 |

## Data

**Included:** `data/wi_2020_cbgs_voting_demo.geojson` holds 4,678 Wisconsin census block groups. It includes population and demographics (2020 PL 94-171, via the Redistricting Data Hub), ward-level election returns disaggregated to CBGs, and the People's Maps Commission seed plan (`dis_id`).

**Not included: the mobility flows.** The paper uses SafeGraph Neighborhood Patterns, whose license does not allow redistribution, even in derived form. Instead, `make_synthetic_flows.py` writes `data/synthetic_flows.npy`, a 4,678 × 4,678 matrix with the same shape, row order, and units:

- flows follow a noisy gravity model: proportional to destination population, divided by (distance + 1 km)², times log-normal noise
- each row is scaled to 10 trips per resident

It exists so the code runs end to end. Interaction ratios computed on it are **not** meaningful.

**Using real flows:** build a matrix in the row order of `cbg_indices_WI_houseDis_pmc_2020.json`, where `flows[o, d]` is the trips from CBG `o` to CBG `d`, then pass `--flows` (or set `FLOWS_MATRIX_PATH`). In the paper, SafeGraph device counts were scaled to population as `device_flows(o,d) × pop(o) / devices(o)` and averaged over the months of 2020. Public, already-scaled flows from the same source are available at the census-tract level in [GeoDS/COVID19USFlows](https://github.com/GeoDS/COVID19USFlows).

## Running

```sh
conda env create -f environment.yml
conda activate interaction-ratio-redistricting
./run.sh                                     # full grid: 18 chains x 1,000 steps
./run.sh --steps 20 --compactness 1 --seeds 2018   # quick check
```

`python run_chains.py --help` lists every option. Biased chains are much slower than unbiased ones, because the random walk takes a few seconds per tree and many trees are rejected. The full grid is meant for a many-core machine.

## Results

`results/` holds the 1,000-step chains from November 2022, computed on the real SafeGraph flows. Chain length and seeds were chosen from earlier exploratory runs, which found that 1,000 steps captured nearly the full range of interaction-ratio values and that the random seed made no substantial difference. Each chain `comp{C}_bias{B}_seed{S}` has:

| File | Contents |
|---|---|
| `_metrics.csv` | per plan: mean Polsby–Popper compactness, efficiency gap, interaction ratio |
| `_assignments.csv.gz` | district of every CBG (`cbg` = flow-matrix row, `geoid`) at every step |

`summary.csv` gives one row per chain.

- The unbiased chains at the 3× compactness bound were byte-for-byte identical to the 5× chains with the same seed, so only the 5× copies are kept.
- The original runs did not seed numpy's random generator, which the biased walk uses, so the biased chains cannot be regenerated exactly. `run_chains.py` now seeds it.

## Credits

Builds on [GerryChain](https://github.com/mggg/gerrychain) by the MGGG Redistricting Lab.
