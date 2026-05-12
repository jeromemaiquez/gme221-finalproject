import rioxarray as rxr
import xarray as xr
import pandas as pd
import geopandas as gpd
from pathlib import Path

def clip_raster(fp_raster: str | Path, gdf_borders: gpd.GeoDataFrame):
    """Clips a raster (xarray.DataArray) using the geometric union of a GeoDataFrame."""
    da = rxr.open_rasterio(fp_raster, masked=True).squeeze()
    borders = gdf_borders.geometry.union_all()
    
    da_clipped = da.rio.clip(borders)
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