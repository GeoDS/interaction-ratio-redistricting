"""Flow-biased spanning trees for ReCom, built on stock GerryChain 0.2.20.

The original experiments ran on a modified copy of GerryChain. This module carries
over every change that affected the chains, without forking the package:

| Original change in the fork                                         | Here                                |
|---------------------------------------------------------------------|-------------------------------------|
| tree.random_spanning_tree gained a `bias` parameter                  | flow_biased_spanning_tree()         |
| tree.bipartition_tree / recursive_tree_part / proposals.recom        | biased_bipartition() passed as      |
|   threaded `bias` through to the spanning-tree function              |   recom's `method` argument         |
| tree.PopulatedGraph read `graph.nodes` instead of `graph.node_indices`| tree returned as a gerrychain Graph,|
|   so it accepted the plain networkx tree built by the biased walk     |   which has node_indices            |

The fork's other edits (debug prints, Partition.export_to_gdf for saving
assignments, list() fixes in uniform_spanning_tree, which these chains never call)
do not change results and are not needed.
"""

from functools import partial

import networkx as nx
import numpy as np
from gerrychain import Graph
from gerrychain.random import random
from gerrychain.tree import bipartition_tree, random_spanning_tree

UNBIASED = -99


def flow_biased_spanning_tree(graph, bias: int):
    """Spanning tree of `graph`, optionally biased toward high-flow edges.

    bias == UNBIASED: GerryChain's own random_spanning_tree (random edge weights,
    then Kruskal's maximum spanning tree). This is standard ReCom.

    Any other bias: a loop-erased random walk (Wilson's algorithm). From each node
    not yet in the tree, step to a neighbour with probability proportional to
    flow_weight ** bias, until the walk reaches the tree. Edges with heavy
    mobility flows are therefore more likely to be kept in the tree, and so less
    likely to be cut into different districts.
    """
    if bias == UNBIASED:
        return random_spanning_tree(graph)

    root = random.choice(list(graph.node_indices))
    tree_nodes = {root}
    next_node = {root: None}

    for node in graph.node_indices:
        u = node
        while u not in tree_nodes:
            neighbours = [nb for _, nb in graph.edges(u)]
            weights = np.array(
                [np.power(graph.edges[u, nb]["flow_weight"], bias) for nb in neighbours]
            )
            next_node[u] = np.random.choice(neighbours, 1, p=weights / weights.sum())[0]
            u = next_node[u]

        u = node
        while u not in tree_nodes:
            tree_nodes.add(u)
            u = next_node[u]

    tree = nx.Graph()
    tree.add_edges_from((n, next_node[n]) for n in tree_nodes if next_node[n] is not None)
    return Graph(tree)


def biased_bipartition(bias: int):
    """A bipartition `method` for gerrychain.proposals.recom that uses the biased tree."""
    return partial(bipartition_tree, spanning_tree_fn=partial(flow_biased_spanning_tree, bias=bias))
