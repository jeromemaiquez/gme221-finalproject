import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib import lines as mlines
from matplotlib.font_manager import FontProperties

# import contextily as cx
# import geopandas as gpd
import pandas as pd
import seaborn as sns
import osmnx as ox
import networkx as nx
import pyfonts
# import pandas as pd
# import geopandas as gpd
from pathlib import Path

def get_edge_widths(
    graph_roads: nx.MultiGraph,
    default_width: float = 0.5
):
    """
    Returns a list of edge widths corresponding to graph edges.
    Written with the help of ChatGPT.
    """
    edge_widths = []
    street_widths = {
        "primary": 2,
        "secondary": 1.5,
        "tertiary": 1,
        "residential": 0.5,
        "unclassified": 1
    }

    for u, v, data in graph_roads.edges(data=True):
        highway = data.get("highway", None)
        
        if isinstance(highway, str):
            width = street_widths.get(highway, default_width)
        elif isinstance(highway, list):
            width = default_width
            for h in highway:
                if h in street_widths:
                    width = street_widths[h]
                    break
        else:
            width = default_width
        
        edge_widths.append(width)
    
    return edge_widths

def plot_graph(
    graph_roads: nx.MultiGraph,
    edge_color: str | dict = "#999999",
    default_width: float = 0.5,
    bg_color: str = "#111111",
    edge_alpha: float = 1.0,
    ax: Axes | None = None,
    bbox: tuple | None = None
):
    """Plots a road network graph."""
    node_size = 0
    show = False

    if not ax:
        _, ax = plt.subplots()
    
    edge_widths = get_edge_widths(graph_roads, default_width)

    _, ax = ox.plot.plot_graph(
        G=graph_roads, 
        edge_linewidth=edge_widths,
        edge_color=edge_color, 
        bgcolor=bg_color,
        node_size=node_size, 
        show=show, ax=ax, figsize=None,
        edge_alpha=edge_alpha,
        bbox=bbox
    )

    return ax

def get_fonts(font_name: str, legend: str = "medium", legend_size: str = "xx-large"):
    """
    Return regular, medium, and bold font versions for a given font name.
    Also, allows the selection of which version to use for the legend.
    """
    font_bold = pyfonts.load_google_font("Fira Sans", weight="bold")
    font_medium = pyfonts.load_google_font("Fira Sans", weight="medium")
    font_regular = pyfonts.load_google_font("Fira Sans", weight="regular")

    match legend:
        case "bold":
            font_legend = font_bold
        case "medium":
            font_legend = font_medium
        case "regular":
            font_legend = font_regular

    font_legend_prop = FontProperties(
        family=font_legend.get_family(),
        weight=font_legend.get_weight(),
        size=legend_size,
        fname=font_legend.get_file()
    )

    return font_bold, font_medium, font_regular, font_legend_prop

def plot_isolated_areas(
        graph_baseline: nx.MultiGraph,
        flooded_graphs: dict[str, nx.MultiGraph],
        isolated_graphs: dict[str, nx.MultiGraph],
        fp_output: str | Path | None = None,
        plot_theme: str = "dark"
):
    """
    Plots the baseline and flooded road networks + isolated areas.
    If an `fp_output` is provided, the plot is saved to a PNG file.
    Parameter `plot_theme` must be `dark` or `light`.
    """
    isolated_color = "#d30000"
    flooded_color = "#1f77b4"

    if plot_theme == "dark":
        bg_color = "#111111"
        ft_color = "#eeeeee"
    elif plot_theme == "light":
        bg_color = "#eeeeee"
        ft_color = "#333333"
    else:
        raise ValueError("Parameter `plot_theme` must be `dark` or `light`.")

    font_bold, font_medium, font_regular, font_legend = get_fonts("Fira Sans")

    # font_bold = pyfonts.load_google_font("Fira Sans", weight="bold")
    # font_medium = pyfonts.load_google_font("Fira Sans", weight="medium")
    # font_regular = pyfonts.load_google_font("Fira Sans", weight="regular")

    # font_medium_legend = FontProperties(
    #     family=font_medium.get_family(),
    #     weight=font_medium.get_weight(),
    #     size="xx-large",
    #     fname=font_regular.get_file()
    # )

    fig, axes = plt.subplots(
        nrows=1,
        ncols=len(flooded_graphs) + 1,
        figsize=(19, 6),
        # layout="constrained",
        facecolor=bg_color
    )

    fig.suptitle(
        "Road Networks and Isolated Areas per Flooding Return Period",
        color=ft_color,
        fontsize=30,
        y=0.95, font=font_bold
    )

    bbox = ox.graph_to_gdfs(graph_baseline, nodes=False).total_bounds

    plot_graph(graph_roads=graph_baseline, ax=axes[0], edge_color=ft_color, bbox=bbox)
    axes[0].set_facecolor(bg_color)
    # axes[0].set_title("No Flooding", color=ft_color)
    axes[0].text(
            0.15, 0.90,
            "No Flood",
            color=ft_color,
            fontsize="x-large",
            transform=axes[0].transAxes,
            font=font_regular
        )

    # Sort return periods into ascending order (not alphabetical)
    return_periods = sorted([int(rp.removesuffix("year")) for rp in flooded_graphs.keys()])

    for ax, rp in zip(axes[1:], return_periods):
        plot_graph(graph_baseline, edge_color=flooded_color, ax=ax)
        plot_graph(flooded_graphs[f"{rp}year"], edge_color=ft_color, ax=ax, bbox=bbox)
        plot_graph(isolated_graphs[f"{rp}year"], edge_color=isolated_color, ax=ax, bbox=bbox)
        ax.text(
            0.15, 0.90,
            f"{rp} year RP Flood",
            color=ft_color,
            fontsize="x-large",
            transform=ax.transAxes,
            font=font_regular
        )
        ax.set_facecolor(bg_color)

    # Create legend icons and labels
    legend_handles = [
        mlines.Line2D([-0.5, 0.5], [0.0, 0.0], color=color, linewidth=2) 
        for color in [ft_color, flooded_color, isolated_color]
    ]
    
    legend_labels = [
        "Non-Flooded Roads",
        "Flooded Roads",  
        "Isolated Areas"
    ]

    fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        ncol=4,
        labelcolor=ft_color,
        fontsize="xx-large",
        facecolor=bg_color,
        edgecolor=bg_color,
        prop=font_legend,
        bbox_to_anchor=(0.5, 0.025)
    )

    plt.subplots_adjust(left=0.01, right=0.975, wspace=0.03)

    if fp_output:
        plt.savefig(fp_output, dpi=300)

    return fig

def plot_betweenness(
        graph_baseline: nx.MultiGraph,
        flooded_graphs: dict[str, nx.MultiGraph],
        betweenness_attr: str = "betweenness",
        fp_output: str | Path | None = None,
        # plot_theme: str = "dark",
        cmap: str = "magma"
):
    """
    Plots the betweenness centrality for baseline and flooded road networks.
    If an `fp_output` is provided, the plot is saved to a PNG file.
    Parameter `plot_theme` must be `dark` or `light`.
    """
    flooded_color = "#1f77b4"

    # if plot_theme == "dark":
    #     bg_color = "#111111"
    #     ft_color = "#999999"
    # elif plot_theme == "light":
    #     bg_color = "#eeeeee"
    #     ft_color = "#333333"
    # else:
    #     raise ValueError("Parameter `plot_theme` must be `dark` or `light`.")

    bg_color = "#000000"
    ft_color = "#eeeeee"

    font_bold, font_medium, font_regular, font_legend = get_fonts("Fira Sans")

    # font_bold = pyfonts.load_google_font("Fira Sans", weight="bold")
    # font_medium = pyfonts.load_google_font("Fira Sans", weight="medium")
    # font_regular = pyfonts.load_google_font("Fira Sans", weight="regular")

    # font_medium_legend = FontProperties(
    #     family=font_medium.get_family(),
    #     weight=font_medium.get_weight(),
    #     size="xx-large",
    #     fname=font_regular.get_file()
    # )

    fig, axes = plt.subplots(
        nrows=1,
        ncols=len(flooded_graphs) + 1,
        figsize=(19, 6),
        # layout="constrained",
        facecolor=bg_color
    )

    fig.suptitle(
        "Betweenness Centrality per Flooding Return Period",
        color=ft_color,
        fontsize=30,
        y=0.95, font=font_bold
    )

    bbox = ox.graph_to_gdfs(graph_baseline, nodes=False).total_bounds

    zero_betweenness = [(u, v) for u, v, attrs in graph_baseline.edges(data=True) if attrs.get(betweenness_attr) == 0]
    graph_filtered = graph_baseline.copy()
    graph_filtered.remove_edges_from(zero_betweenness)
    # print("Is the list of zero betweenness equal to the length of the graph?", len(zero_betweenness) == len(graph_baseline.nodes))
    edge_colors = ox.plot.get_edge_colors_by_attr(
        G=graph_filtered,
        attr=betweenness_attr,
        num_bins=4, 
        cmap=cmap, 
        na_color=ft_color,
        equal_size=True
    )

    plot_graph(graph_baseline, edge_color=bg_color, ax=axes[0], bbox=bbox)
    plot_graph(graph_roads=graph_filtered, ax=axes[0], edge_color=edge_colors, bbox=bbox)
    axes[0].set_facecolor(bg_color)
    axes[0].text(
        0.15, 0.90,
        "No Flood",
        color=ft_color,
        fontsize="x-large",
        transform=axes[0].transAxes,
        font=font_regular
    )

    # Sort return periods into ascending order (not alphabetical)
    return_periods = sorted([int(rp.removesuffix("year")) for rp in flooded_graphs.keys()])

    for ax, rp in zip(axes[1:], return_periods):
        zero_betweenness = [(u, v) for u, v, attrs in flooded_graphs[f"{rp}year"].edges(data=True) if attrs.get(betweenness_attr, 0) == 0]
        graph_filtered = flooded_graphs[f"{rp}year"].copy()
        graph_filtered.remove_edges_from(zero_betweenness)
        edge_colors = ox.plot.get_edge_colors_by_attr(
            G=graph_filtered,
            attr=betweenness_attr,
            num_bins=4, 
            cmap=cmap, 
            na_color=ft_color,
            equal_size=True
        )

        plot_graph(graph_baseline, edge_color=bg_color, ax=ax, bbox=bbox)
        plot_graph(graph_filtered, edge_color=edge_colors, ax=ax, bbox=bbox)
        ax.text(
            0.15, 0.90,
            f"{rp} year RP Flood",
            color=ft_color,
            fontsize="x-large",
            transform=ax.transAxes,
            font=font_regular
        )
        ax.set_facecolor(bg_color)

        legend_handles = [
            mlines.Line2D([-0.5, 0.5], [0.0, 0.0], color=color, linewidth=2) 
            for color in ox.plot.get_colors(n=4, cmap=cmap)
        ]

        legend_labels = [
            # "Very Low",
            "Low",
            "Moderate",
            "High"
        ]

        fig.legend(
            legend_handles[1:],
            legend_labels,
            loc="lower center",
            ncol=4,
            labelcolor=ft_color,
            fontsize="xx-large",
            facecolor=bg_color,
            edgecolor=bg_color,
            prop=font_legend,
            bbox_to_anchor=(0.5, 0.025)
        )

        plt.subplots_adjust(left=0.01, right=0.975, wspace=0.03)

        if fp_output:
            plt.savefig(fp_output, dpi=300)

    return fig

def plot_network_access(network_access_per_rp: dict, fp_output: str | Path | None = None):
    """
    Creates a line plot of network-wide accessibility scores
    for baseline condition and each flooding return period.
    """
    # sns.set_style('whitegrid')
    sns.set_context('talk')
    
    ft_color = "#000000"
    bg_color = "#eeeeee"

    font_bold, font_medium, font_regular, font_legend = get_fonts("Fira Sans")

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    sns.pointplot(
        x=network_access_per_rp.keys(),
        y=network_access_per_rp.values(),
        marker="s",
        # estimator="first", 
        errorbar=None,
        color=ft_color
    )

    plt.suptitle(
        "Network-wide Accessibility across Flooding Return Periods",
        fontsize=24,
        font=font_bold,
        ha="center", y=0.96
    )

    plt.xlabel("Return Period", font=font_medium, fontsize=20)
    plt.ylabel("Network Accessibility", font=font_medium, fontsize=20)
    plt.xticks(ticks=[0, 1, 2, 3], labels=["No Flooding", "5 years", "25 years", "100 years"])

    for rp in network_access_per_rp:
        access_value = network_access_per_rp[rp]
        offset = 7.5
        if rp == "baseline":
            offset = -7.5
        plt.text(
            x=rp,
            y=access_value + offset,
            s=f"{access_value}",
            horizontalalignment="center",
            verticalalignment="center",
            color=bg_color,
            bbox={"facecolor": ft_color, "alpha": 0.8, "edgecolor": "none"},
            fontsize=16,
            font=font_regular
        )

    plt.tight_layout()

    if fp_output:
        plt.savefig(fp_output)
    
    return fig, ax

def plot_potential_access(
        df_entry: pd.GeoDataFrame,
        potential_acc_prefix: str = "pa",
        fp_output: str | Path | None = None
):
    """
    Creates a line plot of potential accessibility scores
    for each major entry point in the road network.
    """
    sns.set_style("whitegrid")
    sns.set_context('talk')
    
    ft_color = "#000000"
    bg_color = "#eeeeee"

    font_bold, font_medium, font_regular, font_legend = get_fonts("Fira Sans")

    pa_cols = [col for col in df_entry.columns if col.startswith(f"{potential_acc_prefix}_")]
    id_cols = [col for col in df_entry.columns if col not in pa_cols]
    df_melt = df_entry.melt(
        id_vars=id_cols, 
        value_vars=pa_cols,
        var_name="rp", 
        value_name="potential_acc",
    )
    df_melt["name"] = df_melt["name"].apply(
        lambda x: x[0] if isinstance(x, list) else x
    )

    fig, ax = plt.subplots(figsize=(12, 6), facecolor=bg_color)
    # sns.pointplot(
    g = sns.catplot(
        kind="point",
        data=df_melt,
        x="rp",
        y="potential_acc",
        # hue="name",
        col="name",
        col_wrap=3,
        marker="s",
        sharey=True,
        sharex=True,
        color=ft_color,
        # estimator="first", 
        errorbar=None,
    )

    g.set_titles("{col_name}", font=font_medium)

    plt.suptitle(
        "Potential Accessibility per Entry Point across Return Periods",
        fontsize=24,
        font=font_bold,
        ha="center", y=0.96
    )

    g.set_axis_labels("Return Period", "Network Accessibility", font=font_medium, fontsize=20)
    g.set_xticklabels(font=font_regular)
    for ax in g.axes.flat:
        for label in ax.get_yticklabels():
            label.set_fontproperties(FontProperties(fname=font_regular.get_file()))
    # plt.ylabel("Network Accessibility", font=font_medium, fontsize=20)
    plt.xticks(ticks=[0, 1, 2, 3], labels=["No Flood", "5 yrs", "25 yrs", "100 yrs"])

    plt.tight_layout()

    if fp_output:
        plt.savefig(fp_output)

    return fig, ax