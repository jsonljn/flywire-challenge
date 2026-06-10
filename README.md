# FlyWire Challenge

## Overview
Finds the largest identical (isomorphic) directed induced subgraph across at least 3 of 5 connectome datasets. 

Standard graph isomorphism is NP-hard. This pipeline avoids combinatorial explosion by searching for independent star topologies (In-Stars and Out-Stars), eliminating the need for expensive permutation matching.

---

## Technical Approach

The pipeline isolates two configurations:
1. **Out-Stars (Broadcast):** One central hub pointing to N independent leaves.
2. **In-Stars (Integration):** N independent leaves pointing to one central hub.

```text
   Out-Star Configuration             In-Star Configuration
   
     [ Leaf 1 ]                         [ Leaf 1 ]
     ^        \                         /        v
    /          v                       v          \
(Hub) ------> [ Leaf 2 ]          [ Leaf 2 ] ------> (Hub)
    \          ^                       ^          /
     v        /                         \        v
     [ Leaf 3 ]                         [ Leaf 3 ]
```

### Constraints & Isomorphism Guarantee
To satisfy induced subgraph rules and allow direct alignment, the pipeline enforces two invariants:
* **Zero Leaf-to-Leaf Edges:** Leaves cannot connect to each other.
* **No Feedback Loops:** Leaves cannot have secondary connections back to the hub.

Because these leaves share zero internal edges, they are topologically symmetric. This allows direct sequential matching between datasets.
