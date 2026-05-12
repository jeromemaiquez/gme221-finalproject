import pandas as pd
import geopandas as gpd
import networkx as nx
from pathlib import Path

import utils
import flood
import population
import models

WORK_DIR = Path().resolve()
DATA_DIR = WORK_DIR / "data"
OUTPUT_DIR = WORK_DIR / "output"

fp_admin = DATA_DIR / "phl_admbnda_adm4_psa_namria_20231106.zip"
fp_output = OUTPUT_DIR / "Antipolo_RoadNetwork.gpkg"
fp_entry = OUTPUT_DIR / "Antipolo_RoadEntryPoints.gpkg"
fps_flood = (DATA_DIR / "flood").glob("*.tif")
fp_pop_raster = DATA_DIR / "phl_pop_2025_CN_100m_R2025A_v1.tif"
fp_pop_points = OUTPUT_DIR / "Antipolo_PopPoints.gpkg"

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

gdf_entry = utils.get_destinations(gdf_edges, gdf_admin)

# Step 4: generate population point grid
da_pop = population.clip_raster(fp_pop_raster, gdf_admin)
gdf_pop = population.raster_to_points(da_pop, value_name="population")

# Assign population to entry points
# gdf_entry = population.nearest_pop_point(gdf_entry, gdf_pop)
gdf_entry = population.voronoi_total_pop_per_dest(g_roads, gdf_entry, gdf_pop)
# gdf_pop.to_file(fp_pop_points)

# Step 5: calculate potential accessibility for baseline conditions
print(f"Is the road network empty? {nx.is_empty(g_roads)}")
baseline_potential_acc = models.potential_accessibility(
    graph_roads=g_roads,
    gdf_orig=gdf_pop,
    gdf_dest=gdf_entry,
    population="population"
)
gdf_entry["pa_baseline"] = gdf_entry.index.map(baseline_potential_acc)

# Step 6: generate flooded versions of original road network

for fp in fps_flood:
    _, _, return_period, _, _ = fp.stem.split("_")
    
    print(f"Analyzing flood return period: {return_period}")
    fp_out_flooded = OUTPUT_DIR / f"Antipolo_RoadNetwork_Flood{return_period}.gpkg"

    # Sample flood depths along road edges for every 20 meters
    edge_depths = flood.get_edge_flood_depths(gdf_edges, fp, step_size=20)
    
    # Remove road edges if its maximum NOAH flood rating >= 2 (at least 0.5 meters) 
    # Excluding primary/secondary highways (to ensure access to entry points)
    graph_flooded = flood.remove_inundated_roads(g_roads, edge_depths, threshold=2)
    # utils.save_graph_geopackage(graph_flooded, fp_out_flooded)

    # Calculate potential accessibility per destination per return period
    potential_acc_per_dest = models.potential_accessibility(
        graph_roads=graph_flooded,
        gdf_orig=gdf_pop,
        gdf_dest=gdf_entry,
        population="population"
    )
    pa_col_name = f"pa_{return_period}"
    gdf_entry[pa_col_name] = gdf_entry.index.map(potential_acc_per_dest)

gdf_entry.to_file(fp_entry)