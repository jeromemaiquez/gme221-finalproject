import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
import numpy as np

# def potential_accessibility(
#         graph_roads: nx.MultiDiGraph, 
#         gdf_orig: gpd.GeoDataFrame,
#         gdf_dest: gpd.GeoDataFrame,   
#         population: str
# ):
#     """
#     Calculates the potential accessibility $\mathit{PA_i}$ for each destination $i$.
#     $$\mathit{PA_i} = \sum_{j} \frac{P_j}{T_{ij}} $$, where: 
#     - $P_j$: population at origin $j$
#     - $T_{ij}$: travel time from j to i 
#     """
#     pa_per_dest = {}

#     for idx, row in gdf_dest.iterrows():
#         dest_node = ox.distance.nearest_nodes(
#             graph_roads, 
#             row["geometry"].x, 
#             row["geometry"].y
#         )

#         orig_nodes = ox.distance.nearest_nodes(
#             graph_roads, 
#             gdf_orig.geometry.x, 
#             gdf_orig.geometry.y
#         )

#         dest_nodes = [dest_node] * len(orig_nodes)
#         # dest_nodes = [dest_node]

#         routes = ox.routing.shortest_path(
#             graph_roads,
#             orig_nodes,
#             dest_nodes,
#             weight="travel_time",
#         )

#         potential_acc = 0

#         for orig_idx, route in enumerate(routes):
#             if route is None or len(route) < 1:
#                 continue

#             if len(route) < 2:
#                 travel_time = 1   # Small value to replace 0
#             else:
#                 gdf_route_edges = ox.routing.route_to_gdf(
#                     graph_roads,
#                     route,
#                     weight="travel_time"
#                 )
#                 travel_time = gdf_route_edges["travel_time"].sum()

#             pop = gdf_orig.iloc[orig_idx][population]
#             potential_acc += pop / travel_time

#         pa_per_dest[idx] = potential_acc
    
#     return pa_per_dest

def potential_accessibility(
        graph_roads: nx.MultiGraph, 
        gdf_orig: gpd.GeoDataFrame,
        gdf_dest: gpd.GeoDataFrame,   
        population: str
):
    """
    Calculates the potential accessibility PA_i for each destination i.
    PA_i = sum_j(P_j / T_ij), where: 
    - P_j: population at origin j
    - T_ij: travel time from j to i 
    
    Refactored for optimization with the help of Claude AI.
    """
    orig_nodes = ox.distance.nearest_nodes(
        graph_roads,
        gdf_orig.geometry.x.to_numpy(),
        gdf_orig.geometry.y.to_numpy()
    )
    populations = gdf_orig[population].to_numpy(dtype=float)

    pa_per_dest = {}

    for idx, row in gdf_dest.iterrows():
        dest_node = ox.distance.nearest_nodes(
            graph_roads,
            row["geometry"].x,
            row["geometry"].y
        )

        # For each dest_node, compute all shortest path lengths in one call
        lengths = nx.single_source_dijkstra_path_length(
            graph_roads, dest_node, weight="length"
        )
        # Then map orig_nodes to their distances
        tt_vals = np.array([lengths.get(n, np.inf) for n in orig_nodes])
        pa_per_dest[idx] = np.sum(populations / np.where(tt_vals < 2, 1.0, tt_vals))

    return pa_per_dest

def network_accessibility(
        gdf_entry: gpd.GeoDataFrame,
        potential_acc_prefix: str = "pa",
        pop_col: str = "population",
        return_periods: list[int] = [5, 25, 100],
        return_period_suffix: str = "year"
):
    """
    Calculates network-wide accessibility A_r for different flooding return periods r.
    A_r = (sum_i(PA_i * P_i)) / sum_i(P_i), where:
    - P_i = total population at destination i
    """
    def network_access_formula(potential_acc: pd.Series | np.ndarray, population: pd.Series | np.ndarray):
        return round(np.sum(potential_acc * population) / np.sum(population), 2)

    network_access_per_rp = {"baseline": network_access_formula(gdf_entry["pa_baseline"], gdf_entry["population"])}

    for rp in return_periods:
        pa_flooded_col = f"{potential_acc_prefix}_{rp}{return_period_suffix}"
        pa_flooded_key = f"{rp}_{return_period_suffix}"

        network_access_per_rp[pa_flooded_key] = network_access_formula(
            gdf_entry[pa_flooded_col],
            gdf_entry["population"]
        )
    
    return network_access_per_rp