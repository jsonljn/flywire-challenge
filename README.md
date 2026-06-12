# FlyWire Qualification Challenge 2026

This repository contains a graph-matching pipeline that identifies an identical induced subgraph across three connectome datasets: FAFB, MCNS, and MAOL.

The pipeline produces a weakly connected, isomorphic subgraph of 2,563 nodes, with identical induced edge patterns (2,586 edges) verified across all three networks.

Matching is based on structural isomorphism only. The selected hub neurons and their roles are not claimed to be biologically homologous; correspondence is by topological role within the constructed circuit, not by cell type or brain region.

## Approach: Root Star + Depth-2 Extension

1. Hub selection: a hub node is chosen per dataset (FAFB: 720575940628908548, MCNS: 10157, MAOL: 10046).

2. Root star (depth-1): the hub's neighbors are reduced to a greedy maximal independent set, so no two selected leaves share an edge with each other. Leaves are split by edge direction relative to the hub:
   - out: hub -> leaf only (1854)
   - in: leaf -> hub only (29)
   - bi: hub <-> leaf, both directions (24)

   The bi leaves introduce 2-cycles with the hub; the structure is not cycle-free.

3. Depth-2 extension: for 655 of the root-out leaves ("parents"), one child node is attached with a single edge child -> parent, where the child has no other edge into the selected set. This is a separate greedy matching step, not an independent set solver.

The counts (1854, 29, 24, 655) are the minimum feasible values found across the three datasets and are fixed in the script.

## Why this is isomorphic

Every node has a fixed structural role, identical across all three datasets:

- Hub: out-degree = 1854 (to out leaves + depth-2 parents) + 24 (to bi leaves), in-degree = 29 (from in leaves) + 24 (from bi leaves)
- Out leaf (non-parent): in-degree = 1, out-degree = 0
- Depth-2 parent: in-degree = 2 (from hub, from child), out-degree = 0
- Depth-2 child: in-degree = 0, out-degree = 1 (to parent)
- In leaf: out-degree = 1, in-degree = 0
- Bi leaf: in-degree = 1, out-degree = 1 (both to/from hub)

Since these counts match across datasets and each role class is internally symmetric (no edges among leaves of the same type), any positional alignment between datasets is a valid isomorphism.

## Validation

The script verifies, for each dataset independently, that the induced edge pattern from the raw CSV matches the expected pattern exactly, that there are no duplicate selected nodes, and that all three datasets produce identical patterns.

Verified output:
```
fafb: unique=2,563 duplicates=0 internal_edges=2,586 matches_expected=True
mcns: unique=2,563 duplicates=0 internal_edges=2,586 matches_expected=True
maol: unique=2,563 duplicates=0 internal_edges=2,586 matches_expected=True
all three induced patterns are identical and weakly connected
```

## Limitations

The hub IDs and target counts are fixed values found by inspecting candidates per dataset and taking the minimum feasible counts across all three. This is a constructed circuit around chosen hubs, not a search over all possible circuit shapes; larger or differently shaped shared circuits may exist.

Possible extensions: deeper chains (depth-3+), multiple stars connected by a spine, or VF2 with degree pruning for arbitrary subgraph isomorphism on smaller candidate sets.

## Requirements

Standard library only (csv, heapq, pathlib). No external dependencies.

## Data Prerequisites

Place the following files in the same directory as the script:
- fafb_783_edge_list.csv
- mcns_0.9_edge_list.csv
- maol_1.1_edge_list.csv

## Usage

```
python solution.py
```

The script loads each graph, builds and verifies the induced subgraph, and writes the result to solution.csv. Runtime is roughly 90 seconds, dominated by CSV parsing of the three multi-million-edge files.

## Results Summary

- Node count: 2,563
- Internal edges: 2,586, identical across all three datasets
- Topology: root star (out/in/bi leaves) with depth-2 extension on 655 leaves
- Connectivity: weakly connected
- Isomorphism: verified programmatically against raw edge lists
