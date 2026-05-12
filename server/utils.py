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
    G = nx.MultiGraph(G)

    return G

def graph_to_gdf(graph: nx.MultiGraph) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Converts a MultiDiGraph to node and/or edge GeoDataFrames, for further processing."""
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(graph)
    return gdf_nodes, gdf_edges

# def save_graph_geopackage(graph: nx.MultiGraph, filepath: str| Path) -> None:
#     """Save graph nodes and edges to disk as layers in a GeoPackage file."""
#     ox.save_graph_geopackage(graph, filepath)

def save_graph_geopackage(graph: nx.MultiGraph, filepath: str| Path) -> None:
    """Save graph nodes and edges to disk as layers in a GeoPackage file."""
    if isinstance(filepath, str):
        not_gpkg = not filepath.endswith(".gpkg")
    elif isinstance(filepath, Path):
        not_gpkg = filepath.suffix != ".gpkg"
    
    if not_gpkg:
        raise ValueError("Output filepath must be GeoPackage (.gpkg)")
    gdf_nodes, gdf_edges = graph_to_gdf(graph)
    gdf_nodes.to_file(filepath, driver="GPKG", layer="nodes")
    gdf_edges.to_file(filepath, driver="GPKG", layer="edges")

def get_destinations(gdf_roads: gpd.GeoDataFrame, gdf_borders: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Returns a GeoDataFrame of the destination points for the road network,
    assumed to be the major (primary/secondary) road-based entry/exit points for the AOI.
    """
    border = gdf_borders.geometry.union_all("coverage").exterior

    gdf_major_roads = gdf_roads[gdf_roads["highway"].isin(["primary", "secondary"])]
    
    gdf_entry_roads = gdf_major_roads[gdf_major_roads.intersects(border)]
    entry_points = gdf_entry_roads.geometry.intersection(border)

    gdf_entry_roads = gpd.GeoDataFrame(
        data=gdf_entry_roads.drop(columns=["geometry"]),
        geometry=entry_points,
        crs=gdf_entry_roads.crs
    )

    return gdf_entry_roads
