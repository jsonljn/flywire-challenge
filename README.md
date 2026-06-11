# FlyWire Qualification Challenge 2026

This repository contains a graph-matching pipeline designed to identify identical induced subgraphs across neural connectome datasets. It aligns data across three datasets: FAFB, MCNS, and MAOL.

The algorithm isolates an isomorphic, weakly connected subgraph consisting of 2,563 nodes, matching structural constraints across all three networks.

## Approach: Depth-2 Star Expansion

The pipeline utilizes a Depth-2 Star Expansion framework:

1. Hub Anchor Selection: The search anchors onto a known homologous neuron hub across the datasets.
2. Induced Subgraph Safety: The algorithm enforces a cycle-free tree topology. Ensuring candidate nodes only connect to their specific parent anchor guarantees that no cross-connections break the isomorphic constraint.
3. Heuristic Independent Set Selection: To maximize valid leaves at Depth-2, the script models neighbor conflicts as a graph and uses a heuristic independent set solver to select the non-conflicting pool of nodes.

## Repository Structure

- flywire_solver.py: The script implementing the 2,563-node greedy star-expansion pipeline.
- README.md: Project documentation.

## Requirements

This project relies entirely on the Python standard library. No external dependencies or package installations are required.

### Data Prerequisites

Place the following dataset files in the root directory alongside the script:
- fafb_783_edge_list.csv
- mcns_0.9_edge_list.csv
- maol_1.1_edge_list.csv

## Usage

Run the production script to execute the pipeline:

    python solution.py

The script will process the graphs, verify the induced subgraph patterns, and output the aligned matrix to solution.csv.

## Results Summary

- Verified Node Count: 2,563 Nodes
- Topology Type: Depth-2 Star Subgraph
- Execution Time: Under 10 Seconds
- Isomorphism: Validated
