# FlyWire Qualification Challenge

## Result

679-node out-star circuit identified across FAFB, BANC, and MCNS. This is the largest shared out-star found under the constraints below, not necessarily the largest isomorphic subgraph of any topology.

| Dataset | Hub Neuron ID | Leaves |
|---------|--------------|--------|
| FAFB | 720575940625525740 | 678 |
| BANC | 720575941604300790 | 678 |
| MCNS | 10157 | 678 |

Cross-dataset matching is based on structural isomorphism — neurons are matched by topological role, not biological identity or brain region.

---

## Approach

General subgraph isomorphism is NP-hard, making exhaustive search infeasible on graphs with 100,000+ nodes. This pipeline searches for out-star topologies: a hub node with directed edges to N independent leaves. Stars are identifiable in linear time and guaranteed isomorphic by construction, making them a practical lower bound on the maximum achievable circuit size.

```
(Hub) ------> [ Leaf 1 ]
(Hub) ------> [ Leaf 2 ]
(Hub) ------> [ Leaf 3 ]
      ...
(Hub) ------> [ Leaf N ]
```

### Isomorphism Guarantee

Within the induced subgraph, every node has a fixed structural role:
- Hub: out-degree = N, in-degree = 0
- Each leaf: in-degree = 1, out-degree = 0

All leaves are structurally symmetric, so any positional alignment between datasets is a valid isomorphism. No permutation search is required.

### Constraints

Two invariants are enforced for every leaf candidate:
1. No leaf-to-leaf edges
2. No feedback edges from leaf to hub

These are required by the induced subgraph condition: all edges between selected nodes in the original graph must be present in the subgraph.

### Search Procedure

All nodes are scanned as hub candidates, sorted by out-degree descending. For each candidate, outgoing neighbors are tested against the two constraints. The hub with the most valid leaves is selected. This establishes maximality within the star topology — no other hub in these datasets yields a larger valid out-star.

---

## Complexity

Adjacency construction is O(E). The hub scan runs in O(deg²) per candidate, with early termination and degree-sorted ordering. In practice this completes in seconds on graphs with 6M+ edges.

---

## Limitations & Extensions

This finds the largest star-shaped isomorphic circuit, not the globally largest. Possible extensions in order of complexity:

- 2-hop stars: expand leaves to include their own out-neighbors, forming a two-level tree
- Small DAG expansion: greedily add edges between leaf pairs and test if isomorphism holds
- VF2 with degree pruning: searches arbitrary subgraph isomorphisms; feasible up to ~20-30 nodes
- Frequent subgraph mining: methods like gSpan enumerate recurring motifs across multiple graphs

---

## Usage

Requirements:
```
pip install pandas numpy
```

Files needed:
```
fafb_783_edge_list.csv
banc_626_edge_list.csv
mcns_0.9_edge_list.csv
maol_1.1_edge_list.csv
manc_1.2.1_edge_list.csv
```

Run:
```
python flywire_solution.py
```

Outputs `solution.csv` — 679 rows × 3 columns (fafb, banc, mcns). Row 1 = matched hubs. Rows 2–679 = matched leaves.
