## Overview
This project aims to **analyze the impacts of flood inundation** on **road-based accessibility** in lowland Antipolo City, Rizal.

## Environment Setup
- Python 3.x
- [put environments here]

## How to Run
1. Activate the virtual environment
2. Run `analysis.py` to run the full spatial statistical analysis pipeline

## Objectives
#### Measure the impact of flooding on the road network accessibility in lowland Antipolo
1. **Model road disruption** due to flooding via **road network edge removal**
2. **Calculate accessibility** for **baseline vs. flooded** road network conditions
3. **Identify isolated areas along the road network** under flooding conditions

## Methodology
1. Download & pre-process road network in AOI
    - Simplify nodes
    - Assign edge lengths, speed, and travel time
2. Remove inundated road segments for different flood return periods
    - Flood threshold: NOAH flood category $\geq 2$ ($\geq 0.5$ meters flood depth)
    - ...Which corresponds to the MMDA threshold for NPAV flood rating (not passable to ALL types of vehicles)
    - BONUS: Will compute betweenness centrality before & after removal of inundated segments
3. Compute accessibility index (before & after flooding)
    - Destinations: major road-based entry points into AOI
    - Origins: population grid centroids
    - Potential accessibility per Destination i: $$ \mathit{PA_i} = \sum_{j} \frac{P_j}{T_{ij}} $$

    > - $P_j =$ population size at origin j
    >
    > - $T_{ij} =$ travel time from j to i

    - Network-wide accessibility for multiple flooding return periods r (or baseline scenario 0): $$ A_r = \frac{\sum_{i} \mathit{PA_i} \times P_i}{\sum_{i} P_i} $$

    > - $P_i$ = population size at destination i

4. Identify areas isolated due to flooding (and measure their population size)

## Assumptions
- Primary and secondary roads assumed to never get inundated to the point of being impassable (only for analysis purposes)
- Only entry points along primary & secondary roads are included (excluded tertiary entry points)
- Assumes bidirectional roads (one-way roads not modeled) to prevent doubling of entry points in bidirectional roads with no middle island

## Outputs
- Charts/tables of accessibility metrics
- Map of betweenness centrality on road network
- Map of areas isolated from the wider road network

## Reflections 
