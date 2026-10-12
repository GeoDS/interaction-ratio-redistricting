"""Generate a synthetic CBG-to-CBG flow matrix in place of the licensed SafeGraph data.

The real matrix (2020 monthly-average SafeGraph Neighborhood Patterns flows, scaled to
population) cannot be redistributed. This builds a stand-in with the same shape, index
order, and dtype using a noisy gravity model, so every script in this folder runs.
Results computed on it are illustrative only and will not match the paper.
"""

import json
from pathlib import Path

import geopandas as gpd
import numpy as np

DATA = Path(__file__).parent / "data"
TRIPS_PER_PERSON = 10
SEED = 2023


def main() -> None:
    cbgs = gpd.read_file(DATA / "wi_2020_cbgs_voting_demo.geojson").to_crs("EPSG:3071")
    index = json.loads((DATA / "cbg_indices_WI_houseDis_pmc_2020.json").read_text())
    cbgs["row"] = cbgs["geoid"].astype("int64").astype(str).map(index)
    cbgs = cbgs.sort_values("row")
    assert cbgs["row"].tolist() == list(range(len(index))), "GeoJSON and index file disagree"

    pop = cbgs["population"].to_numpy(dtype=float)
    xy = np.column_stack([cbgs.centroid.x, cbgs.centroid.y]) / 1000
    dist_km = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(axis=-1))

    rng = np.random.default_rng(SEED)
    attraction = pop[None, :] / (dist_km + 1.0) ** 2
    attraction *= rng.lognormal(mean=0.0, sigma=1.0, size=attraction.shape)
    flows = attraction / attraction.sum(axis=1, keepdims=True) * (pop * TRIPS_PER_PERSON)[:, None]

    out = DATA / "synthetic_flows.npy"
    np.save(out, flows)
    print(f"wrote {out} {flows.shape}, {flows.sum():,.0f} total trips")


if __name__ == "__main__":
    main()
