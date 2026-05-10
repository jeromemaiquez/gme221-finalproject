import pandas as pd
import geopandas as gpd
from pathlib import Path

import utils as u

WORK_DIR = Path().resolve()
DATA_DIR = WORK_DIR / "data"
OUTPUT_DIR = WORK_DIR / "output"

fp_admin = DATA_DIR / "phl_admbnda_adm4_psa_namria_20231106.zip"
fp_output = OUTPUT_DIR / "Antipolo_RoadNetwork.gpkg"

# Step 1: define AOI

gdf_admin = gpd.read_file(f"zip://{fp_admin}")

barangays = ["Mayamot", "Cupang", "Mambugan"]
city = "City of Antipolo"

gdf_admin = gdf_admin[(gdf_admin["ADM4_EN"].isin(barangays)) & (gdf_admin["ADM3_EN"] == city)]

# Step 2: download road network + get nodes & edges as GeoDataFrames

g_roads = u.get_road_network(gdf_admin)

gdf_nodes, gdf_edges = u.graph_to_gdf(g_roads)

# save_graph_geopackage(g_roads, fp_output)