import rioxarray as rxr
import xarray as xr
import numpy as np
import geopandas as gpd
from shapely import to_geojson
import geojson
import networkx as nx
import osmnx as ox
from pathlib import Path

def clip_raster(fp_raster: str | Path, gdf_borders: gpd.GeoDataFrame):
    """Clips a raster (xarray.DataArray) using the geometric union of a GeoDataFrame."""
    da = rxr.open_rasterio(fp_raster, masked=True)
    borders = [geojson.loads(to_geojson(gdf_borders.geometry.make_valid(method="structure").union_all()))]
    
    da_clipped = da.rio.clip(borders, crs=gdf_borders.crs).squeeze()
    return da_clipped

def raster_to_points(da_raster: xr.DataArray, value_name: str = "population"):
    """Converts a raster (xarray.DataArray) into a grid of points (gpd.GeoDataFrame)."""
    df = da_raster.to_dataframe(name=value_name).reset_index()
    df = df.dropna(subset=[value_name])

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.x, df.y),
        crs=da_raster.rio.crs
    )

    return gdf

def nearest_pop_point(gdf_entry: gpd.GeoDataFrame, gdf_pop: gpd.GeoDataFrame, pop_col: str = "population"):
    """Assigns to an entry point the population value of its nearest population grid point."""
    gdf_join = gdf_entry.to_crs("EPSG:32651").sjoin_nearest(
        gdf_pop[["population", "geometry"]].to_crs("EPSG:32651"), 
        how="left", 
        max_distance=100    # 100 meters (pixel size of pop. grid)
    ).to_crs("EPSG:4326")

    dict_aggfunc = {col: "first" for col in gdf_entry}
    dict_aggfunc[pop_col] = "sum"

    gdf_join = gdf_join.groupby(by=["u", "v", "key"]).agg(dict_aggfunc).reset_index()
    gdf_join = gpd.GeoDataFrame(
        data=gdf_join,
        geometry=gdf_join["geometry"],
        crs="EPSG:4326"
    )

    return gdf_join

def voronoi_total_pop_per_dest(
        graph_roads: nx.MultiGraph, 
        gdf_entry: gpd.GeoDataFrame, 
        gdf_pop: gpd.GeoDataFrame, 
        pop_col: str = "population"
):
    """
    Assigns each population grid point to the nearest AOI entry point,
    then takes the sum of all pop. grid points with the same nearest entry point.
    Designed for optimization with the help of Claude AI
    """
    orig_nodes = ox.distance.nearest_nodes(
        graph_roads,
        gdf_pop.geometry.x.to_numpy(),
        gdf_pop.geometry.y.to_numpy()
    )
    populations = gdf_pop[pop_col].to_numpy(dtype=float)

    dest_nodes = ox.distance.nearest_nodes(
        graph_roads,
        gdf_entry.geometry.x.to_numpy(),
        gdf_entry.geometry.y.to_numpy()
    )
    dest_indices = list(gdf_entry.index)

    # Single Dijkstra sweep per destination
    # Shape: 10 dests x 25k origins
    dist_matrix = np.full((len(dest_nodes), len(orig_nodes)), np.inf)

    for i, dest_node in enumerate(dest_nodes):
        lengths = nx.single_source_dijkstra_path_length(
            graph_roads, dest_node, weight="travel_time"
        )
        dist_matrix[i] = [lengths.get(n, np.inf) for n in orig_nodes]

    # For each origin, find the index of the closest destination
    nearest_dest_idx = np.argmin(dist_matrix, axis=0)   # shape: (25k,)

    # Sum populations grouped by assigned destination
    total_pop_per_dest = {}
    for i, dest_idx in enumerate(dest_indices):
        mask = nearest_dest_idx == i
        total_pop_per_dest[dest_idx] = populations[mask].sum()

    gdf_join = gdf_entry.copy(deep=True)
    gdf_join["population"] = gdf_join.index.map(total_pop_per_dest)

    return gdf_join

