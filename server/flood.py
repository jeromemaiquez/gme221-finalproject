import pandas as pd
import geopandas as gpd
import numpy as np
import rasterio as rio
import networkx as nx
from pathlib import Path

def generate_sampling_points(gdf_edges: gpd.GeoDataFrame, step_size: int) -> dict[tuple, list]:
    """Generates unique sampling points along road geometries"""
    points_map = {}
    for idx, row in gdf_edges.iterrows():
        line = row.geometry
        # Sample at intervals, always including start (0) and end (length)
        distances = np.unique(np.append(np.arange(0, line.length, step_size), line.length))
        for d in distances:
            pt = line.interpolate(d)
            coord = (pt.x, pt.y)
            if coord not in points_map:
                points_map[coord] = []
            points_map[coord].append(idx)
    return points_map

def get_edge_flood_depths(gdf_edges: gpd.GeoDataFrame, raster_path: str | Path, step_size: int) -> dict:
    """Samples raster depths along edges and returns the maximum depth per edge."""
    points_map = generate_sampling_points(gdf_edges.to_crs("EPSG:32651"), step_size)
    unique_pts = list(points_map)

    print(f"Sampling {len(unique_pts)} points from raster...")
    with rio.open(raster_path) as src:
        depths = [val[0] if val[0] != 255 else 0 for val in src.sample(unique_pts)]

    edge_depths = {idx: 0.0 for idx in gdf_edges.index}
    for coord_idx, depth in enumerate(depths):
        if depth is not None:
            coord = unique_pts[coord_idx]
            for edge_id in points_map[coord]:
                edge_depths[edge_id] = max(edge_depths[edge_id], depth)
    
    return edge_depths

def remove_inundated_roads(graph_roads: nx.MultiGraph, edge_depths: dict, threshold: int = 2.0) -> nx.MultiGraph:
    """Returns a flooded version of the original road network, where flooded roads are deemed impassable and removed."""
    # flooded_edges = [idx for idx, d in edge_depths.items() if d >= threshold]

    protected_highways = {"primary", "secondary"}

    flooded_edges = []

    for edge_id, depth in edge_depths.items():
        if depth < threshold:
            continue

        # Get highway type per road edge
        u, v, k = edge_id
        edge_data = graph_roads[u][v][k]
        highway = edge_data.get("highway")

        # Check if highway type is protected
        if isinstance(highway, list):
            is_protected = any(h in protected_highways for h in highway)
        else:
            is_protected = highway in protected_highways

        if not is_protected:
            flooded_edges.append(edge_id)

    graph_flooded = graph_roads.copy()
    graph_flooded.remove_edges_from(flooded_edges)

    return graph_flooded