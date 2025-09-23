# standard
import os
import re
import sys
# external
import plotly
import polars as pl
from polars import col
# local
src_path = os.path.abspath("elf_smi/src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import plot


################
# Translations #
################

TRANSLATION_MAP = {
    "Selguseta ala": "renewal not complete",
    "Lage ala": "clearcut",
    "Kokku": "all",
    "Haab": "aspen",
    "Kask": "birch",
    "Sanglepp": "black alder",
    "Hall lepp": "grey alder",
    "Teised": "other",
    "Mänd": "pine",
    "Kuusk": "spruce",
    "all": "kokku",
    "aspen": "haab",
    "birch": "kask",
    "black alder": "sanglepp",
    "grey alder": "hall_lepp",
    "other": "teised",
    "pine": "mänd",
    "spruce": "kuusk"
}


#########
# Input #
#########

# --[ paths
ROOT_DIR_PATH = "elf_smi"
DIAMETER_PATH = "data/clean/diameter.csv"
PLOT_SAVE_DIR_PATH = "result"


# --[ analysis parameters
COMPARISON_SPECIES = ["pine"]
DIAMETER_AGGREGATION_MAP = {
    "0...2":            "0...10",
    "3...4":            "0...10",
    "5...6":            "0...10",
    "7...8":            "0...10",
    "9...10":           "0...10",
    "11...12":          "11...18",
    "13...14":          "11...18",
    "15...16":          "11...18",
    "17...18":          "11...18",
    "19...20":          "19...24",
    "21...22":          "19...24",
    "23...24":          "19...24",
    "25...26":          "25...28",
    "27...28":          "25...28",
    "29...30":          "29...34",
    "31...32":          "29...34",
    "33...34":          "29...34",
    "35...36":          "35...",
    "37...38":          "35...",
    "39...40":          "35...",
    "41...42":          "35...",
    "43...44":          "35...",
    "45...46":          "35...",
    "47...48":          "35...",
    "49...50":          "35...",
    "51...":            "35...",
}

# --[ plot parameters
PLOT_TITLE = "Metsamaa pindalad keskmise diameetri järgi"
X_AXIS_TITLE = "Aasta"
Y_AXIS_TITLE = "pindala (tuhat ha)"
LEGEND_diameter_groupS_TITLE = "Diameetri grupp:"
SOURCE_ANNOTATIONS = (
    "diameetri andmed: https://tableau.envir.ee/views/SMI/10Diameetrid?%3Aembed=y<br>"
    "analüüs: https://github.com/martroben/forest_analysis/tree/main/elf_smi/<br>"
    "skript: src/07_plot_diameters.py"
    # ^ Added as annotations to the plot image
)
LEGEND_COLORSCALE = "Greys"
SPECIES_COLORSCALES = [
    # uses plotly colorscales: https://plotly.com/python/builtin-colorscales/
    # DOMINANT_SPECIES       # COLORSCALE
    ("all",                  "algae"),
    ("aspen",                "Purples"),
    ("birch",                "speed"),
    ("black alder",          "turbid"),
    ("grey alder",           "YlOrBr"),
    ("other",                "Greys"),
    ("pine",                 "amp"),
    ("spruce",               "tempo"),
]


#############
# Load data #
#############

DIAMETER_PATH = os.path.join(ROOT_DIR_PATH, DIAMETER_PATH)
with open(DIAMETER_PATH, encoding="utf-8") as read_file:
    diameter_data = pl.read_csv(read_file)


##################
# Get areas data #
##################

# Aggregate age groups
diameter_aggregated = plot.aggregate_diameter_groups(diameter_data, DIAMETER_AGGREGATION_MAP)
area_data = (
    diameter_aggregated
    .filter(
        col("DIAMETER_CM_GROUP") != "all"
    )
    .pivot(
        index=["YEAR", "UNIT", "DOMINANT_SPECIES"],
        on="DIAMETER_CM_GROUP",
        values="AREA",
        sort_columns=True
    )
    .with_columns(pl.exclude("YEAR").fill_null(0.0))
    .sort(col("YEAR"))
)


#########################
# Collect unique inputs #
#########################

unique_species = (
    area_data
    .select(col("DOMINANT_SPECIES"))
    .unique()
    .to_series()
    .to_list()
)
unique_years = (
    area_data
    .select(col("YEAR"))
    .unique()
    .sort(col("YEAR"))
    .to_series()
    .to_list()
)
unique_diameter_groups = sorted(
    set(DIAMETER_AGGREGATION_MAP.values()),
    # Sort ascending by group start age
    key=lambda x: int(re.search(r"\d+", x).group())
)
# Maximum bar heights by species
max_areas = dict(
    diameter_data
    .group_by([
        col("DOMINANT_SPECIES"),
        col("YEAR")
    ])
    .agg(AREA=col("AREA").sum())
    .group_by(col("DOMINANT_SPECIES"))
    .agg(AREA=col("AREA").max())
    .iter_rows()
)


###############
# Get colours #
###############

species_colorscales = {}
for row in SPECIES_COLORSCALES:
    species, colorscale = row
    species_colorscales[species] = colorscale

legend_colours = plot.get_colours(
    n=len(unique_diameter_groups),
    scale_name=LEGEND_COLORSCALE
)

title_colours = {}
for species, colorscale in species_colorscales.items():
    colours = plot.get_colours(5, colorscale)
    title_colours[species] = colours[3]


##############
# Get traces #
##############

# --[ strategy
# Each year (1999 / 2000 etc.) is a separate group of bars on the plot.
# Each selected species (pine, birch etc.) is a separate grouped bar under a year.
# Each diameter group (0...10 / 11...18 etc.) is a section in the stacked bars.
# To display legend, we add extra traces with no points on plot - just colours.
# Altogether, there is a trace for each (species, diameter group) combination + legend traces.

traces = []

# --[ area traces
for species in COMPARISON_SPECIES:
    species_colours = plot.get_colours(
        n=len(unique_diameter_groups),
        scale_name=species_colorscales[species]
    )
    diameter_group_colour_map = dict(zip(unique_diameter_groups, species_colours))

    trace_data = (
        area_data
        .filter(
            col("DOMINANT_SPECIES") == species,
        )
        .to_dict(as_series=False)
    )
    for diameter_group in unique_diameter_groups:
        trace = plotly.graph_objects.Bar(
            x=trace_data["YEAR"],
            y=trace_data[diameter_group],
            name=diameter_group,
            marker_color=diameter_group_colour_map[diameter_group],
            showlegend=False
        )
        # Set offsetgroup only if there are more than 1 comparison species.
        # Otherwise the year labels don't line up with bars for a single species.
        if len(COMPARISON_SPECIES) > 1:
            trace.offsetgroup = species
        traces += [trace]

# --[ legend traces
legend_colour_map = dict(zip(unique_diameter_groups, legend_colours))
for diameter_group in unique_diameter_groups:
    traces += [
        plotly.graph_objects.Bar(
            x=[None], y=[None],
            name=diameter_group,
            marker_color=legend_colour_map[diameter_group],
            showlegend=True,
            legendgroup="diameter_groups",
            legendgrouptitle={
                "text": LEGEND_diameter_groupS_TITLE,
                "font": {"size": 28}
            }
        )
    ]


###################
# Get plot layout #
###################

comparison_species_translated = [TRANSLATION_MAP[species] for species in COMPARISON_SPECIES]
plot_title_text = f'{PLOT_TITLE}: {" | ".join(comparison_species_translated)}'
substring_colour_map = {TRANSLATION_MAP[species]: title_colours[species] for species in COMPARISON_SPECIES}

plot_title = plot.apply_colour_to_substring(
    plot_title_text,
    substring_colour_map
)
layout = plot.get_layout(
    title=plot_title,
    x_axis_title=X_AXIS_TITLE,
    y_axis_title=Y_AXIS_TITLE,
    source_annotations=SOURCE_ANNOTATIONS,
    x_range=(min(unique_years), max(unique_years)),
    y_range=(0, max([max_areas[species] for species in COMPARISON_SPECIES]))
)
# Ad hoc patch to make the bars thinner for single species graphs
if len(COMPARISON_SPECIES) == 1:
    layout.bargap = 0.7

##############
# Save plots #
##############

figure = plotly.graph_objects.Figure(
    traces,
    layout
)
filename = f'diameetrid_{"_".join(comparison_species_translated)}.png'
save_path = os.path.join(ROOT_DIR_PATH, PLOT_SAVE_DIR_PATH, filename)

os.makedirs(
    os.path.dirname(save_path),
    exist_ok=True
)
plotly.io.write_image(
    figure,
    save_path,
    format="png"
)
