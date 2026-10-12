# Bringing Spatial Interaction Measures into Multi-Criteria Assessment of Redistricting Plans

**Jacob Kruse, Song Gao, Yuhan Ji, Daniel P. Szabo, Kenneth Mayer** · GeoDS Lab, University of Wisconsin–Madison

[**🗺️ View the interactive web map →**](https://krusejake.github.io/wi-redistricting-tradeoffs-explorer/)

| | |
|---|---|
| **Paper** | *Cartography and Geographic Information Science*, 51(4), 513–532 · [doi:10.1080/15230406.2023.2264750](https://doi.org/10.1080/15230406.2023.2264750) |
| **Preprint** | [arXiv:2309.13480](https://arxiv.org/abs/2309.13480) |
| **Code** | [`methods/`](methods/): an implementation of the methodology. It is **not** a replication package: settings differ from the paper, and it ships with synthetic mobility flows |

## Overview

Redistricting criteria often ask that *communities of interest* be kept together, but common proxies such as geometric compactness and municipal splits capture this poorly. We propose the **interaction ratio (IR)**: the total human-mobility flow *within* districts divided by the total flow *between* districts, computed from large-scale mobility data. It measures how well a plan preserves communities that actually interact.

Using the ReCom Markov chain algorithm, we generate ensembles of valid Wisconsin congressional plans at the census block group level. We then compare IR against compactness and partisan fairness (efficiency gap), and introduce two methods that bias sampling toward higher or lower values of a criterion.

## Methods

### Data

| Input | Source | Unit |
|---|---|---|
| Human mobility flows | SafeGraph Neighborhood Patterns, monthly for 2020, averaged into one origin–destination matrix | Census block group (CBG) |
| Population & geometry | 2020 Census redistricting data (PL 94-171), via the Redistricting Data Hub | CBG |
| Election returns | 2018 U.S. House results, disaggregated from wards to CBGs by citizen population aged 18+ | CBG |

Device-level flows (with flows from fewer than 4 devices removed) are scaled to population flows following Kang et al. (2020):

$$\text{flow}_{pop}(o,d) = \text{flow}_{device}(o,d) \times \frac{\text{pop}(o)}{\text{devices}(o)}$$

### Evaluation criteria

| Criterion | Definition |
|---|---|
| **Interaction ratio (IR)** | $\displaystyle IR = \frac{\sum \text{intra-district flows}}{\sum \text{inter-district flows}}$ (higher means districts better contain the communities people actually travel within) |
| **Compactness** | Polsby–Popper score, $4\pi A / P^2$ |
| **Partisan fairness** | Efficiency gap, $(W_D - W_R) / V$, where $W$ is wasted votes and $V$ is total votes. Seat outcomes are also tallied against the proportional 4–4 split. |

### Ensemble generation

- Plans are sampled with the **ReCom** Markov chain (via [GerryChain](https://github.com/mggg/gerrychain)). Each step merges two adjacent districts, draws a spanning tree over the merged CBGs, and cuts it into two population-balanced districts.
- All chains start from the **People's Maps Commission (PMC)** plan, which is designed to keep communities of interest intact.
- Constraints are contiguity, a population deviation of at most 3%, and a cut-edge compactness bound of 1× or 5× the seed plan.
- Six chains of 10,000 steps each were run:

  | Compactness bound | Chains |
  |---|---|
  | 1× (tight) | baseline ReCom · biased spanning tree (+100) · max-IR cut |
  | 5× (loose) | baseline ReCom · biased spanning tree (−100) · min-IR cut |

### Biasing toward (or away from) interaction

Two modifications steer the chain toward plans with higher or lower IR:

1. **Biased spanning tree:** each edge's random weight is multiplied by its mobility flow and a bias term (±100) before the maximum spanning tree is drawn. Strongly connected CBGs are then less likely to be separated by the cut.
2. **Max-/min-IR cut:** draw a spanning tree as usual, enumerate every valid cut, and keep the cut that most increases (or decreases) IR.

Biased and unbiased ensembles are compared with Kolmogorov–Smirnov tests.

## Key results

- **Biasing works.** Both methods shift the IR distribution significantly (KS *p* < 0.001). Under the tighter compactness bound, the maximum IR rises from 3.77 (unbiased) to 3.90 (biased spanning tree), moving roughly 550,000 trips from between-district to within-district.
- **IR and compactness move together:** more compact plans tend to keep mobility communities intact.
- **Proportionality:** the high-IR, high-compactness ensemble produces more proportional 4–4 seat splits than the low-IR, low-compactness ensemble.
- **Usability:** a 10-participant user study found high task accuracy with the web map. The 3-D values cube was the hardest component to use.

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
| `methods/` | Ensemble and interaction-ratio code, input data, and earlier chain outputs. See [`methods/README.md`](methods/README.md) |

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
