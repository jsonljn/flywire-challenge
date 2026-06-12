from __future__ import annotations

import csv
import heapq
from pathlib import Path


DATASETS = {
    "fafb": "fafb_783_edge_list.csv",
    "mcns": "mcns_0.9_edge_list.csv",
    "maol": "maol_1.1_edge_list.csv",
}

HUBS = {
    "fafb": 720575940628908548,
    "mcns": 10157,
    "maol": 10046,
}

ROOT_COUNTS = {
    "out": 1854,
    "in": 29,
    "bi": 24,
}

DEPTH2_COUNT = 655
TRIPLE = ["fafb", "mcns", "maol"]
OUTPUT = Path("network.csv")


def load_graph(path: Path):
    id_to_idx = {}
    idx_to_id = []
    out = []
    adj = []
    self_loop_nodes = set()

    def idx(node_id: int) -> int:
        node_idx = id_to_idx.get(node_id)
        if node_idx is None:
            node_idx = len(idx_to_id)
            id_to_idx[node_id] = node_idx
            idx_to_id.append(node_id)
            out.append(set())
            adj.append(set())
        return node_idx

    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            src = int(row["source neuron id"])
            tgt = int(row["target neuron id"])
            src_idx = idx(src)
            tgt_idx = idx(tgt)
            out[src_idx].add(tgt_idx)

            if src_idx == tgt_idx:
                self_loop_nodes.add(src_idx)
                continue

            adj[src_idx].add(tgt_idx)
            adj[tgt_idx].add(src_idx)

    return id_to_idx, idx_to_id, out, adj, self_loop_nodes


def greedy_independent_set(vertices, adj):
    candidates = set(vertices)
    degree = {vertex: len(adj[vertex] & candidates) for vertex in candidates}
    heap = [(deg, vertex) for vertex, deg in degree.items()]
    heapq.heapify(heap)
    chosen = []

    while heap:
        deg, vertex = heapq.heappop(heap)
        if vertex not in candidates or degree.get(vertex) != deg:
            continue

        chosen.append(vertex)
        removed = (adj[vertex] & candidates) | {vertex}
        for removed_vertex in removed:
            candidates.discard(removed_vertex)

        touched = set()
        for removed_vertex in removed:
            touched |= adj[removed_vertex] & candidates

        for touched_vertex in touched:
            new_degree = len(adj[touched_vertex] & candidates)
            if new_degree != degree.get(touched_vertex):
                degree[touched_vertex] = new_degree
                heapq.heappush(heap, (new_degree, touched_vertex))

    return chosen


def classify(a: int, b: int, out) -> str:
    a_to_b = b in out[a]
    b_to_a = a in out[b]

    if a_to_b and b_to_a:
        return "bi"
    if a_to_b:
        return "out"
    if b_to_a:
        return "in"
    return "none"


def root_star(id_to_idx, idx_to_id, out, adj, self_loop_nodes, name: str):
    hub_idx = id_to_idx[HUBS[name]]
    leaves = greedy_independent_set(
        [vertex for vertex in adj[hub_idx] if vertex not in self_loop_nodes],
        adj,
    )

    by_type = {"out": [], "in": [], "bi": []}
    for leaf_idx in leaves:
        by_type[classify(hub_idx, leaf_idx, out)].append(leaf_idx)

    for leaf_type in by_type:
        by_type[leaf_type].sort(key=lambda vertex: idx_to_id[vertex])
        by_type[leaf_type] = by_type[leaf_type][: ROOT_COUNTS[leaf_type]]

    selected = {hub_idx} | set(by_type["out"]) | set(by_type["in"]) | set(by_type["bi"])
    return hub_idx, by_type, selected


def choose_depth2_pairs(idx_to_id, out, adj, self_loop_nodes, root_out_leaves, selected):
    """
    Choose parent-child pairs where each parent is a root-out leaf and the child
    has exactly one edge to the current root star: child -> parent.
    """
    selected_neighbor_count = [0] * len(idx_to_id)
    for selected_vertex in selected:
        for neighbor in adj[selected_vertex]:
            selected_neighbor_count[neighbor] += 1

    options = []
    for parent in root_out_leaves:
        candidates = []
        for child in adj[parent]:
            if child in selected or child in self_loop_nodes:
                continue
            if selected_neighbor_count[child] != 1:
                continue
            if classify(parent, child, out) == "in":
                candidates.append(child)

        if candidates:
            options.append((len(candidates), parent, candidates))

    options.sort(key=lambda item: (item[0], idx_to_id[item[1]]))

    chosen = []
    chosen_children = set()
    for _, parent, candidates in options:
        candidates.sort(key=lambda vertex: (len(adj[vertex]), idx_to_id[vertex]))

        chosen_child = None
        for child in candidates:
            if adj[child] & chosen_children:
                continue
            chosen_child = child
            break

        if chosen_child is not None:
            chosen.append((parent, chosen_child))
            chosen_children.add(chosen_child)

    if len(chosen) < DEPTH2_COUNT:
        raise RuntimeError(f"Only found {len(chosen)} depth-2 pairs; need {DEPTH2_COUNT}")

    return chosen[:DEPTH2_COUNT]


def select_dataset(name: str):
    print(f"Loading {name}...")
    id_to_idx, idx_to_id, out, adj, self_loop_nodes = load_graph(Path(DATASETS[name]))
    hub_idx, by_type, selected = root_star(id_to_idx, idx_to_id, out, adj, self_loop_nodes, name)
    depth2_pairs = choose_depth2_pairs(
        idx_to_id,
        out,
        adj,
        self_loop_nodes,
        by_type["out"],
        selected,
    )

    depth2_parents = {parent for parent, _ in depth2_pairs}
    remaining_out = [leaf for leaf in by_type["out"] if leaf not in depth2_parents]

    print(
        f"  hub={HUBS[name]} "
        f"root_out={len(by_type['out'])} "
        f"root_in={len(by_type['in'])} "
        f"root_bi={len(by_type['bi'])} "
        f"depth2_pairs={len(depth2_pairs)}"
    )

    return {
        "hub": idx_to_id[hub_idx],
        "depth2_parents": [idx_to_id[parent] for parent, _ in depth2_pairs],
        "remaining_out": [idx_to_id[leaf] for leaf in remaining_out],
        "in": [idx_to_id[leaf] for leaf in by_type["in"]],
        "bi": [idx_to_id[leaf] for leaf in by_type["bi"]],
        "depth2_children": [idx_to_id[child] for _, child in depth2_pairs],
    }


def write_solution(selected):
    rows = []
    rows.append({name: selected[name]["hub"] for name in TRIPLE})

    for idx in range(DEPTH2_COUNT):
        rows.append({name: selected[name]["depth2_parents"][idx] for name in TRIPLE})

    remaining_out_count = ROOT_COUNTS["out"] - DEPTH2_COUNT
    for idx in range(remaining_out_count):
        rows.append({name: selected[name]["remaining_out"][idx] for name in TRIPLE})

    for idx in range(ROOT_COUNTS["in"]):
        rows.append({name: selected[name]["in"][idx] for name in TRIPLE})

    for idx in range(ROOT_COUNTS["bi"]):
        rows.append({name: selected[name]["bi"][idx] for name in TRIPLE})

    for idx in range(DEPTH2_COUNT):
        rows.append({name: selected[name]["depth2_children"][idx] for name in TRIPLE})

    with OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TRIPLE)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {OUTPUT} with {len(rows):,} rows.")
    return rows


def expected_pattern():
    expected = set()

    # Root -> all root-out leaves, including depth-2 parents.
    for row_idx in range(1, 1 + ROOT_COUNTS["out"]):
        expected.add((0, row_idx))

    cursor = 1 + ROOT_COUNTS["out"]

    # Root-in leaves.
    for row_idx in range(cursor, cursor + ROOT_COUNTS["in"]):
        expected.add((row_idx, 0))
    cursor += ROOT_COUNTS["in"]

    # Bidirectional root leaves.
    for row_idx in range(cursor, cursor + ROOT_COUNTS["bi"]):
        expected.add((0, row_idx))
        expected.add((row_idx, 0))
    cursor += ROOT_COUNTS["bi"]

    # Depth-2 child -> parent edges. Parent rows are 1..DEPTH2_COUNT.
    for pair_idx in range(DEPTH2_COUNT):
        parent_row = 1 + pair_idx
        child_row = cursor + pair_idx
        expected.add((child_row, parent_row))

    return expected


def verify_solution(rows):
    expected = expected_pattern()
    patterns = {}

    print("Verifying induced directed patterns...")
    for name in TRIPLE:
        nodes = [row[name] for row in rows]
        selected = set(nodes)
        index = {node_id: row_idx for row_idx, node_id in enumerate(nodes)}
        pattern = set()
        raw_internal_rows = 0

        with Path(DATASETS[name]).open(newline="") as f:
            for row in csv.DictReader(f):
                src = int(row["source neuron id"])
                tgt = int(row["target neuron id"])
                if src in selected and tgt in selected:
                    pattern.add((index[src], index[tgt]))
                    raw_internal_rows += 1

        patterns[name] = pattern
        duplicate_count = len(nodes) - len(selected)
        print(
            f"  {name}: unique={len(selected):,} "
            f"duplicates={duplicate_count:,} "
            f"internal_edges={len(pattern):,} "
            f"raw_internal_rows={raw_internal_rows:,} "
            f"matches_expected={pattern == expected}"
        )

        if duplicate_count:
            raise RuntimeError(f"{name} has duplicate selected nodes")
        if pattern != expected:
            extra = len(pattern - expected)
            missing = len(expected - pattern)
            raise RuntimeError(f"{name} mismatch: extra={extra}, missing={missing}")

    if not (patterns["fafb"] == patterns["mcns"] == patterns["maol"]):
        raise RuntimeError("induced patterns are not mutually identical")

    print("  all three induced patterns are identical (weakly connected by construction)")


def main():
    selected = {name: select_dataset(name) for name in TRIPLE}
    rows = write_solution(selected)
    verify_solution(rows)


if __name__ == "__main__":
    main()
