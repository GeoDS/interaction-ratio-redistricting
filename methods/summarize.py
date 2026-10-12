"""Summarize every *_metrics.csv in a results folder into summary.csv."""

import re
import sys
from pathlib import Path

import pandas as pd

NAME = re.compile(r"comp(?P<compactness_bound>\d+)_bias(?P<bias>-?\d+)_seed(?P<seed>\d+)_metrics\.csv")


def main(folder: Path) -> None:
    rows = []
    for path in sorted(folder.glob("*_metrics.csv")):
        config = {k: int(v) for k, v in NAME.fullmatch(path.name).groupdict().items()}
        m = pd.read_csv(path)
        rows.append(
            config
            | {"plans": len(m)}
            | {f"ir_{stat}": getattr(m.interaction_ratio, stat)() for stat in ("min", "median", "max")}
            | {"compactness_median": m.compactness.median(), "efficiency_gap_median": m.efficiency_gap.median()}
        )
    summary = pd.DataFrame(rows).sort_values(["compactness_bound", "bias", "seed"])
    summary.to_csv(folder / "summary.csv", index=False, float_format="%.4f")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "output"))
