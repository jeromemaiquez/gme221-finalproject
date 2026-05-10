import osmnx as ox
import networkx as nx
import geopandas as gpd
from pathlib import Path

def get_road_network(gdf: gpd.GeoDataFrame) -> nx.MultiDiGraph:
    """Downloads the road network inside a given geopandas.GeoDataFrame."""
    print(f"Downloading road network...")
    polygon = gdf.geometry.union_all("coverage")

    G = ox.graph_from_polygon(
        polygon, 
        network_type="all", 
        simplify=True,
        truncate_by_edge=True
    )
    G = ox.distance.add_edge_lengths(G)
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)

    return G

def save_graph_geopackage(graph: nx.MultiDiGraph, filepath: str| Path) -> None:
    """Save graph nodes and edges to disk as layers in a GeoPackage file."""
    ox.save_graph_geopackage(graph, filepath)