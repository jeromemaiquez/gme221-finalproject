import numpy as np
import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import lines as mlines
from pathlib import Path

import utils
import flood
import population
import models
import visualization as viz

WORK_DIR = Path().resolve()
DATA_DIR = WORK_DIR / "data"
OUTPUT_DIR = WORK_DIR / "output"

fp_admin = DATA_DIR / "phl_admbnda_adm4_psa_namria_20231106.zip"
fp_output = OUTPUT_DIR / "Antipolo_RoadNetwork.gpkg"
fp_entry = OUTPUT_DIR / "Antipolo_RoadEntryPoints.gpkg"
fps_flood = (DATA_DIR / "flood").glob("*.tif")
fp_pop_raster = DATA_DIR / "phl_pop_2025_CN_100m_R2025A_v1.tif"
fp_pop_points = OUTPUT_DIR / "Antipolo_PopPoints.gpkg"

fp_isolated_map = OUTPUT_DIR / "Antipolo_MapIsolatedNetwork.png"
fp_between_map = OUTPUT_DIR / "Antipolo_MapBetweennessCentrality.png"
fp_network_plot = OUTPUT_DIR / "NetworkAccess_PerFloodRP.png"
fp_potential_plot = OUTPUT_DIR / "PotentialAccess_PerEntryPoint.png"

# Step 1: define AOI

gdf_admin = gpd.read_file(f"zip://{fp_admin}")

barangays = ["Mayamot", "Cupang", "Mambugan"]
city = "City of Antipolo"

gdf_admin = gdf_admin[(gdf_admin["ADM4_EN"].isin(barangays)) & (gdf_admin["ADM3_EN"] == city)]

# Step 2: download road network + get nodes & edges as GeoDataFrames

g_roads = utils.get_road_network(gdf_admin)
gdf_nodes, gdf_edges = utils.graph_to_gdf(g_roads)

# Step 3: get destination points for accessibility analysis (major entry points into AOI)

gdf_entry = utils.get_destinations(gdf_edges, gdf_admin)
gdf_entry["name"] = [
    "Marcos Highway - Cubao Eastbound",
    "Sumulong Highway - Antipolo",
    "Marcos Highway - Cogeo",
    "B. V. Soliven Avenue",
    "Marcos Highway - Cubao Westbound",
    "Sumulong Highway - Marikina",
]

# Step 4: generate population point grid
da_pop = population.clip_raster(fp_pop_raster, gdf_admin)
gdf_pop = population.raster_to_points(da_pop, value_name="population")

# Assign betweenness centrality to road network edges
g_roads = models.betweenness_centrality(g_roads, gdf_entry, gdf_pop)
utils.save_graph_geopackage(g_roads, fp_output)
# gdf_pop.to_file(fp_pop_points)

# Assign population to entry points
# gdf_entry = population.nearest_pop_point(gdf_entry, gdf_pop)
gdf_entry = population.voronoi_total_pop_per_dest(g_roads, gdf_entry, gdf_pop)

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

flooded_graphs = {}
isolated_graphs = {}

for fp in fps_flood:
    _, _, return_period, _, _ = fp.stem.split("_")
    
    print(f"Analyzing flood return period: {return_period}")
    fp_out_flooded = OUTPUT_DIR / f"Antipolo_RoadNetwork_Flood{return_period}.gpkg"
    fp_out_isolated = OUTPUT_DIR / f"Antipolo_IsolatedNetwork_Flood{return_period}.gpkg"

    # Sample flood depths along road edges for every 20 meters
    edge_depths = flood.get_edge_flood_depths(gdf_edges, fp, step_size=20)
    
    # Remove road edges if its maximum NOAH flood rating >= 2 (at least 0.5 meters) 
    # Excluding primary/secondary highways (to ensure access to entry points)
    graph_flooded = flood.remove_inundated_roads(g_roads, edge_depths, threshold=2)
    graph_flooded = models.betweenness_centrality(graph_flooded, gdf_entry, gdf_pop)
    flooded_graphs[return_period] = graph_flooded
    utils.save_graph_geopackage(graph_flooded, fp_out_flooded)

    graph_isolated = models.isolated_areas(graph_flooded)
    isolated_graphs[return_period] = graph_isolated
    utils.save_graph_geopackage(graph_isolated, fp_out_isolated)

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

network_access = models.network_accessibility(gdf_entry)
# print(network_access)

change_in_access = models.change_in_network_access(network_access)
print(change_in_access)

# Step 7. Plot isolated areas
viz.plot_isolated_areas(
    graph_baseline=g_roads,
    flooded_graphs=flooded_graphs,
    isolated_graphs=isolated_graphs,
    fp_output=fp_isolated_map,
    plot_theme="light"
)

viz.plot_betweenness(
    graph_baseline=g_roads,
    flooded_graphs=flooded_graphs,
    fp_output=fp_between_map,
    # plot_theme="light",
    cmap="inferno"
)

viz.plot_network_access(
    # network_access,
    change_in_access,
    fp_network_plot
)

viz.plot_potential_access(
    gdf_entry,
    fp_output=fp_potential_plot
)