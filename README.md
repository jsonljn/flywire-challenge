# FlyWire Qualification Challenge 2026

**Result:** 2,563 nodes · 2,586 induced edges · identical structure across FAFB, MCNS, and MAOL

## Overview
This repository presents a deterministic graph construction pipeline that identifies a large, identical induced subgraph across three connectome datasets: FAFB, MCNS, and MAOL.

The solution produces a weakly connected, structurally isomorphic circuit of 2,563 nodes and 2,586 edges, with exact induced edge-pattern matching verified directly against the raw datasets.

Critically, this approach avoids the intractability of general subgraph isomorphism by constructing a topology where correctness is guaranteed by design, rather than discovered through search.

## Core Strategy
Subgraph isomorphism is NP-hard in general. Instead of searching arbitrary subgraphs, this solution constrains the search space to a topology that enforces isomorphism structurally.

The circuit is built using three key components:
- Hub-centered star
- Maximal independent leaf set
- Strict depth-2 extensions

These constraints ensure zero accidental cross-connections, fully controlled edge patterns, and guaranteed induced subgraph equivalence across datasets. Rather than verifying candidate subgraphs after construction, this method constructs only valid subgraphs, eliminating combinatorial explosion entirely.

## Topology

```
                         hub
           _____________|_____________
          /      |      |      \      \
      out leaf  ...   in leaf  bi leaf  ...
         |
      (parent row 1-655)
         ^
         |
    depth-2 child (rows 1908-2562)
```

- Rows 1–1854: hub → leaf (out leaves, including depth-2 parents)
- Rows 1855–1883: leaf → hub (in leaves)
- Rows 1884–1907: hub ↔ leaf (bi leaves)
- Rows 1908–2562: child → parent (655 depth-2 chains; parent is row 1 + pair index)

## How it works

### 1. Loading the graph

Each edge list CSV is read once. Every neuron ID is mapped to a compact integer index (`id_to_idx` / `idx_to_id`), since the raw IDs are large integers and indexing by them directly is slower.

Two adjacency structures are built per node:
- `out`: the directed out-neighbors, i.e. `out[a]` contains `b` if the edge a -> b exists.
- `adj`: a symmetrized (undirected) adjacency. For every directed edge a -> b, both `adj[a]` and `adj[b]` get the other node added. So `adj[a]` contains every node connected to `a` by an edge in either direction.

If a row has the same source and target (a self-loop), it is recorded in `out` but not added to `adj`, and the node is marked in `self_loop_nodes`. Self-loop nodes are excluded later when choosing leaves and depth-2 children, because a self-loop edge would add an extra edge to the induced subgraph that the expected pattern does not account for, which would fail verification.

### 2. Root star via greedy independent set

A hub node is chosen per dataset:
- FAFB: 720575940628908548
- MCNS: 10157
- MAOL: 10046

These hubs were selected during exploratory analysis of high-degree candidates: each has a large neighborhood, and together they support the circuit sizes in the counts table below after taking minima across datasets. The IDs are hardcoded constants, not chosen at runtime.

The hub's neighbors (in `adj`, excluding self-loop nodes) are reduced to a greedy maximal independent set: a set of nodes with no edge between any two of them, in either direction.

The greedy heuristic repeatedly picks the remaining candidate with the fewest remaining candidate neighbors, adds it to the result, then removes it and all of its neighbors from further consideration (a node that conflicts with an already-chosen node can no longer be chosen). Degrees of affected nodes are updated and the process repeats until no candidates remain. Picking low-degree nodes first tends to produce a larger independent set, since each pick removes fewer other options.

Because every pair of selected leaves has no edge between them in either direction, the only edges any selected leaf can have within the final subgraph are to the hub itself.

### 3. Classifying leaves by edge direction

For each leaf in the independent set, `classify(hub, leaf, out)` checks the directed `out` sets to determine the relationship:
- out: hub -> leaf exists, leaf -> hub does not
- in: leaf -> hub exists, hub -> leaf does not
- bi: both hub -> leaf and leaf -> hub exist
- none: neither edge exists (not used further)

### 4. Fixed counts and truncation

Each leaf-type list is sorted by the leaf's original neuron ID (ascending) and truncated to a fixed count that is the same across all three datasets:
- out: 1854
- in: 29
- bi: 24

These counts are fixed constants in the script (see "How the counts were derived" below), not computed at runtime from a single dataset. Truncating each dataset's own sorted list to the same count means each dataset contributes the same number of out/in/bi leaves, even though the specific neurons selected differ between datasets.

### 5. Depth-2 extension

For 655 of the root-out leaves (called "parents"), one additional node (a "child") is attached with a single edge child -> parent.

A candidate child for a given parent must satisfy all of:
- not already part of the root star, and not a self-loop node
- have exactly one neighbor (in the symmetrized `adj` sense) among the root-star nodes selected so far -- this guarantees the child's only connection to the rest of the circuit is through this one parent
- classify(parent, child, out) == "in", i.e. the directed edge child -> parent exists and parent -> child does not

Parents are processed in order of how many valid candidate children they have (fewest first), then by parent ID. For each parent, candidate children are sorted by their symmetrized degree (lowest first) then by ID, and the first candidate not already adjacent to a previously chosen child is selected. This greedy matching avoids assigning a child that would conflict with another already-chosen child.

This step is independent of the independent-set step in step 2; it is a separate greedy matching procedure, not another independent-set computation.

After this step, the 655 chosen parents are set aside as "depth-2 parents", and the remaining out-leaves (1854 - 655 = 1199) become "remaining out leaves".

### 6. Assembling the output

Rows are written in a fixed order, identical across all three datasets:

| Rows | Count | Content | Role |
|---|---|---|---|
| 0 | 1 | hub | hub |
| 1-655 | 655 | depth-2 parents | out leaf, also has a depth-2 child |
| 656-1854 | 1199 | remaining out leaves | out leaf, no depth-2 child |
| 1855-1883 | 29 | in leaves | in leaf |
| 1884-1907 | 24 | bi leaves | bi leaf |
| 1908-2562 | 655 | depth-2 children | depth-2 child |

Total rows: 1 + 655 + 1199 + 29 + 24 + 655 = 2563.

Each row has one entry per dataset (fafb, mcns, maol), giving the neuron ID that fills that structural role in that dataset. The specific neuron IDs differ between datasets; the role each row plays in the circuit is identical.

## Edge pattern

The induced subgraph contains 2,586 edges, all identical in structure across the three datasets:

- hub -> each row in 1-1854 (1854 edges): covers depth-2 parents and remaining out leaves
- each row in 1855-1883 -> hub (29 edges): in leaves
- hub -> each row in 1884-1907, and each row in 1884-1907 -> hub (24 x 2 = 48 edges): bi leaves
- each row in 1908-2562 -> its corresponding parent row in 1-655 (655 edges): depth-2 children

1854 + 29 + 48 + 655 = 2586.

No other edges exist within the induced subgraph; this is what the verification step checks for each dataset.

## Why this is isomorphic

Every node has a fixed structural role, identical across all three datasets:

- Hub: out-degree = 1854 (to rows 1-1854) + 24 (to bi leaves) = 1878, in-degree = 29 (from in leaves) + 24 (from bi leaves) = 53
- Out leaf, remaining (rows 656-1854): in-degree = 1 (from hub), out-degree = 0
- Depth-2 parent (rows 1-655): in-degree = 2 (from hub, from its child), out-degree = 0
- Depth-2 child (rows 1908-2562): in-degree = 0, out-degree = 1 (to its parent)
- In leaf (rows 1855-1883): out-degree = 1 (to hub), in-degree = 0
- Bi leaf (rows 1884-1907): in-degree = 1, out-degree = 1, both to/from hub

Within each role class, all members are mutually interchangeable: no edges exist between any two members of the same class, and their connections to the rest of the circuit are identical in count and direction. The specific neuron filling a given row differs between datasets, but since the role-class sizes (1, 655, 1199, 29, 24, 655) are fixed constants applied identically to all three datasets, row index defines the isomorphism map directly — no general subgraph-isomorphism search is needed.

## Connectivity

The circuit is weakly connected by construction: in the underlying undirected graph, every row-1-1854 node (out leaves and depth-2 parents), every in leaf, and every bi leaf is directly connected to the hub. Every depth-2 child (rows 1908-2562) is connected to its parent (one of rows 1-655), which is itself connected to the hub. So every node is within 2 steps of the hub, ignoring direction. The verification step does not re-check connectivity separately; it follows from this layout.

## How the counts were derived

For each dataset, the unconstrained greedy independent set on the hub's neighborhood gives a raw count per leaf type (out/in/bi), and a raw depth-2 feasible pair count (computed after truncating to the chosen ROOT_COUNTS). Each used value is the minimum of that quantity across the three datasets:

| Category | FAFB | MCNS | MAOL | Used (min) |
|---|---|---|---|---|
| out | 1854 | 2208 | 1944 | 1854 |
| in | 254 | 210 | 29 | 29 |
| bi | 2214 | 2234 | 24 | 24 |
| depth-2 | 655 | 684 | 966 | 655 |

Total = 1 (hub) + 1854 + 29 + 24 + 655 = 2563.

MAOL is the limiting dataset for in/bi leaves (its hub has far fewer reciprocal connections than FAFB or MCNS); FAFB is the limiting dataset for out leaves and depth-2 chains.

## Determinism

All sorting in the pipeline is by original neuron ID (ascending), and the greedy heuristics process candidates in a fixed order (by candidate-count, then degree, then ID, as described above). Running the script again on the same input files produces the same output.

## Validation

The script reconstructs the exact set of edges the chosen rows should produce (`expected_pattern`, derived directly from the row layout above), then scans each dataset's raw CSV and builds the actual induced edge pattern over the selected nodes. For each dataset it checks: no duplicate nodes were selected, the actual induced pattern matches the expected pattern exactly, and all three datasets' patterns are identical to each other.

Verified output:
```
fafb: unique=2,563 duplicates=0 internal_edges=2,586 matches_expected=True
mcns: unique=2,563 duplicates=0 internal_edges=2,586 matches_expected=True
maol: unique=2,563 duplicates=0 internal_edges=2,586 matches_expected=True
all three induced patterns are identical (weakly connected by construction)
```

## Limitations

The hub IDs and target counts are fixed values found by computing the raw independent-set and depth-2 counts per dataset and taking the minimum feasible counts across all three. This is a constructed circuit around chosen hubs, not a search over all possible circuit shapes; larger or differently shaped shared circuits may exist.

Possible extensions: deeper chains (depth-3+), multiple stars connected by a spine, or VF2 with degree pruning for arbitrary subgraph isomorphism on smaller candidate sets.

## Requirements

Standard library only (csv, heapq, pathlib). No external dependencies.

## Data Prerequisites

Place the following files in the same directory as the script:
- fafb_783_edge_list.csv
- mcns_0.9_edge_list.csv
- maol_1.1_edge_list.csv

Each file is a CSV with header "source neuron id,target neuron id" and one directed edge per row.

## Output format

The script writes `network.csv` with one row per structural role and three columns (`fafb`, `mcns`, `maol`). Row index is the isomorphism map: the same row index in each dataset plays the same role in the circuit.

```csv
fafb,mcns,maol
720575940628908548,10157,10046
720575940603404834,21615,23597
...
```

A precomputed `network.csv` (2,563 data rows) is included in this repository so reviewers can inspect the result without downloading the edge lists. Re-run `solution.py` to regenerate it when the input CSVs are present.

## Usage

```
python solution.py
```

The script loads each graph, builds and verifies the induced subgraph, and writes the result to `network.csv`. Runtime is roughly 90 seconds, dominated by CSV parsing of the three multi-million-edge files.

## Results Summary

- Node count: 2,563
- Internal edges: 2,586, identical across all three datasets
- Topology: root star (out/in/bi leaves) with depth-2 extension on 655 leaves
- Connectivity: weakly connected
- Isomorphism: verified programmatically against raw edge lists
