import pandas as pd
import geopandas as gpd
from pathlib import Path

import utils
import flood

WORK_DIR = Path().resolve()
DATA_DIR = WORK_DIR / "data"
OUTPUT_DIR = WORK_DIR / "output"

fp_admin = DATA_DIR / "phl_admbnda_adm4_psa_namria_20231106.zip"
fp_output = OUTPUT_DIR / "Antipolo_RoadNetwork.gpkg"
fp_entry = OUTPUT_DIR / "Antipolo_RoadEntryPoints.gpkg"
fps_flood = (DATA_DIR / "flood").glob("*.tif")

# Step 1: define AOI

gdf_admin = gpd.read_file(f"zip://{fp_admin}")

barangays = ["Mayamot", "Cupang", "Mambugan"]
city = "City of Antipolo"

gdf_admin = gdf_admin[(gdf_admin["ADM4_EN"].isin(barangays)) & (gdf_admin["ADM3_EN"] == city)]

# Step 2: download road network + get nodes & edges as GeoDataFrames

g_roads = utils.get_road_network(gdf_admin)

gdf_nodes, gdf_edges = utils.graph_to_gdf(g_roads)

# utils.save_graph_geopackage(g_roads, fp_output)

# Step 3: get destination points for accessibility analysis (major entry points into AOI)

# gdf_entry = utils.get_destinations(gdf_edges, gdf_admin)

# gdf_entry.to_file(fp_entry)

# Step 4: generate flooded versions of original road network

for fp in fps_flood:
    _, _, return_period, _, _ = fp.stem.split("_")
    
    print(f"Analyzing flood return period: {return_period}")
    fp_out_flooded = OUTPUT_DIR / f"Antipolo_RoadNetwork_Flood{return_period}.gpkg"

    # Sample flood depths along road edges for every 20 meters
    edge_depths = flood.get_edge_flood_depths(gdf_edges, fp, step_size=20)
    
    # Remove road edges if its maximum NOAH flood rating >= 2 (at least 0.5 meters) 
    # Excluding primary/secondary highways (to ensure access to entry points)
    graph_flooded = flood.remove_inundated_roads(g_roads, edge_depths, threshold=2)
    utils.save_graph_geopackage(graph_flooded, fp_out_flooded)
