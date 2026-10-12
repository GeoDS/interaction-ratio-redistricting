"""Run ReCom chains over Wisconsin census block groups and score every plan.

One chain runs for each combination of --biases x --compactness x --seeds. Each
chain writes two files to --out:

    comp{C}_bias{B}_seed{S}_metrics.csv          step, compactness, efficiency_gap, interaction_ratio
    comp{C}_bias{B}_seed{S}_assignments.csv.gz   district of every CBG at every step
"""

import argparse
import json
import os
from functools import partial
from itertools import product
from multiprocessing import Pool
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from gerrychain import Election, GeographicPartition, Graph, MarkovChain, accept, constraints
from gerrychain import metrics, updaters
from gerrychain.proposals import recom
from gerrychain.random import random

from biased_tree import UNBIASED, biased_bipartition
from interaction_ratio import interaction_ratio

HERE = Path(__file__).parent
# The only island in the CBG adjacency graph is joined to this block group.
ISLAND_ANCHOR_GEOID = 550291001002
EPSILON = 0.02
POPULATION_TOLERANCE = 0.01
NODE_REPEATS = 2


def build_graph(geojson: Path, index: dict[str, int], flows: np.ndarray) -> Graph:
    cbgs = gpd.read_file(geojson)
    cbgs.loc[~cbgs.is_valid, "geometry"] = cbgs.loc[~cbgs.is_valid, "geometry"].buffer(0)
    graph = Graph.from_geodataframe(cbgs.to_crs("EPSG:3071"), adjacency="queen")

    by_geoid = {graph.nodes[n]["geoid"]: n for n in graph}
    components = sorted(nx.connected_components(graph), key=len)
    for island in components[:-1]:
        graph.add_edge(by_geoid[ISLAND_ANCHOR_GEOID], next(iter(island)))

    for o, d in graph.edges:
        row_o = index[str(int(graph.nodes[o]["geoid"]))]
        row_d = index[str(int(graph.nodes[d]["geoid"]))]
        graph.edges[o, d]["flow_weight"] = max(flows[row_o, row_d] + flows[row_d, row_o], 1.0)
    return graph


def run_chain(config: dict) -> str:
    bias, compactness, seed = config["bias"], config["compactness"], config["seed"]
    random.seed(seed)
    np.random.seed(seed)

    flows = np.load(config["flows"])
    index = json.loads(Path(config["index"]).read_text())
    graph = build_graph(config["geojson"], index, flows)
    rows = np.array([index[str(int(graph.nodes[n]["geoid"]))] for n in graph])
    geoids = [int(graph.nodes[n]["geoid"]) for n in graph]

    initial = GeographicPartition(
        graph,
        assignment="dis_id",
        updaters={
            "population": updaters.Tally("population", alias="population"),
            "HOUSE18": Election("HOUSE18", {"Democratic": "USHDEM18", "Republican": "USHREP18"}),
        },
    )
    ideal_population = sum(initial["population"].values()) / len(initial)
    chain = MarkovChain(
        proposal=partial(
            recom,
            pop_col="population",
            pop_target=ideal_population,
            epsilon=EPSILON,
            node_repeats=NODE_REPEATS,
            method=biased_bipartition(bias),
        ),
        constraints=[
            constraints.within_percent_of_ideal_population(initial, POPULATION_TOLERANCE),
            constraints.UpperBound(
                lambda p: len(p["cut_edges"]), compactness * len(initial["cut_edges"])
            ),
        ],
        accept=accept.always_accept,
        initial_state=initial,
        total_steps=config["steps"],
    )

    metrics_rows, assignments = [], []
    for step, partition in enumerate(chain):
        by_row = np.empty(len(rows), dtype=int)
        by_row[rows] = [partition.assignment[n] for n in graph]
        metrics_rows.append(
            {
                "step": step,
                "compactness": np.mean(list(metrics.polsby_popper(partition).values())),
                "efficiency_gap": metrics.efficiency_gap(partition["HOUSE18"]),
                "interaction_ratio": interaction_ratio(by_row, flows),
            }
        )
        assignments.append(by_row)

    name = f"comp{compactness}_bias{bias}_seed{seed}"
    out = Path(config["out"])
    pd.DataFrame(metrics_rows).to_csv(out / f"{name}_metrics.csv", index=False)
    table = pd.DataFrame(np.column_stack(assignments), columns=[f"step_{i}" for i in range(len(assignments))])
    table.insert(0, "geoid", pd.Series(geoids, index=rows).sort_index().to_numpy())
    table.insert(0, "cbg", np.arange(len(rows)))
    table.to_csv(out / f"{name}_assignments.csv.gz", index=False)
    return name


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--geojson", default=HERE / "data/wi_2020_cbgs_voting_demo.geojson")
    parser.add_argument("--index", default=HERE / "data/cbg_indices_WI_houseDis_pmc_2020.json")
    parser.add_argument("--flows", default=os.environ.get("FLOWS_MATRIX_PATH", HERE / "data/synthetic_flows.npy"))
    parser.add_argument("--out", default=HERE / "output")
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--biases", type=int, nargs="+", default=[UNBIASED, 1],
                        help=f"{UNBIASED} = standard ReCom; otherwise the flow exponent")
    parser.add_argument("--compactness", type=int, nargs="+", default=[1, 3, 5],
                        help="cut-edge bound as a multiple of the seed plan's cut edges")
    parser.add_argument("--seeds", type=int, nargs="+", default=[2018, 1776, 1993])
    parser.add_argument("--workers", type=int, default=os.cpu_count())
    args = parser.parse_args()

    Path(args.out).mkdir(parents=True, exist_ok=True)
    configs = [
        {"bias": b, "compactness": c, "seed": s, "steps": args.steps, "out": args.out,
         "geojson": args.geojson, "index": args.index, "flows": args.flows}
        for b, c, s in product(args.biases, args.compactness, args.seeds)
    ]
    with Pool(min(args.workers, len(configs))) as pool:
        for name in pool.imap_unordered(run_chain, configs):
            print(f"finished {name}", flush=True)


if __name__ == "__main__":
    main()
