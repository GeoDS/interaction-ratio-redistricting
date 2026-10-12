# Bringing Spatial Interaction Measures into Multi-Criteria Assessment of Redistricting Plans

**Jacob Kruse, Song Gao, Yuhan Ji, Daniel P. Szabo, Kenneth Mayer** · GeoDS Lab, University of Wisconsin–Madison

[**🗺️ View the interactive web map →**](https://krusejake.github.io/wi-redistricting-tradeoffs-explorer/)

| | |
|---|---|
| **Paper** | *Cartography and Geographic Information Science*, 51(4), 513–532 · [doi:10.1080/15230406.2023.2264750](https://doi.org/10.1080/15230406.2023.2264750) |
| **Preprint** | [arXiv:2309.13480](https://arxiv.org/abs/2309.13480) |
| **Earlier version** | AutoCarto 2022 · [abstract](https://cartogis.org/docs/autocarto/2022/docs/abstracts/Session6_Kruse_9440.pdf) · [slides](https://cartogis.org/docs/autocarto/2022/docs/presentations/session6_kruse_presentation.pdf) |

## Overview

Redistricting criteria often ask that *communities of interest* be kept together, but common proxies such as geometric compactness and municipal splits capture this poorly. We propose the **interaction ratio (IR)**: the total human-mobility flow *within* districts divided by the total flow *between* districts, computed from large-scale mobility data. It measures how well a plan preserves communities that actually interact.

Using the ReCom Markov chain algorithm, we generate ensembles of valid Wisconsin congressional plans at the census block group level. We then compare IR against compactness and partisan fairness (efficiency gap), and introduce two methods that bias sampling toward higher or lower values of a criterion.

## Key results

- Both biasing methods steer the ensemble toward plans with the targeted criterion values.
- Plans with **higher interaction ratio and compactness** tend, on average, to produce **more proportional seat outcomes** between the two major parties.
- The tradeoffs between criteria can be explored interactively in the web map, which compares the 2022 enacted map against plans that maximize IR, compactness, or efficiency gap.

## The web map

[krusejake.github.io/wi-redistricting-tradeoffs-explorer](https://krusejake.github.io/wi-redistricting-tradeoffs-explorer/) lets you:

- view any two district plans side by side, synchronized, and color them by a chosen metric
- compare district metrics across plans in a linked parallel-coordinates plot
- rotate a 3-D "values cube" of sampled plans to see where each plan sits relative to reasonable alternatives

## Repository contents

| Path | Contents |
|---|---|
| `index.html`, `js/`, `css/`, `lib/` | Web map: Leaflet, D3, and Plotly |
| `data/` | District plans (enacted, max-IR, max-compactness, max-efficiency-gap, PMC) as GeoJSON, plus ward election data |
| `figure_*.html` | Interactive Plotly figures, including the 3-D values cube |
| `img/` | Figures and explanatory graphics |

## Citation

```bibtex
@article{kruse2024redistricting,
  title   = {Bringing spatial interaction measures into multi-criteria assessment of redistricting plans using interactive web mapping},
  author  = {Kruse, Jacob and Gao, Song and Ji, Yuhan and Szabo, Daniel P. and Mayer, Kenneth},
  journal = {Cartography and Geographic Information Science},
  volume  = {51},
  number  = {4},
  pages   = {513--532},
  year    = {2024},
  doi     = {10.1080/15230406.2023.2264750}
}
```
