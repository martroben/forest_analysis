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
AGE_GROUP_PATH = "data/clean/age_group.csv"
PLOT_SAVE_DIR_PATH = "result"

# --[ analysis parameters
COMPARISON_SPECIES = ["birch", "pine", "aspen"]

AGE_GROUP_AGGREGATION_MAP = {
    TRANSLATION_MAP["Lage ala"]:        "0...20",
    TRANSLATION_MAP["Selguseta ala"]:   "0...20",
    "...10":                            "0...20",
    "11...20":                          "0...20",
    "21...30":                          "21...40",
    "31...40":                          "21...40",
    "41...50":                          "41...60",
    "51...60":                          "41...60",
    "61...70":                          "61...80",
    "71...80":                          "61...80",
    "81...90":                          "81...",
    "91...100":                         "81...",
    "101...110":                        "81...",
    "111...120":                        "81...",
    "121...130":                        "81...",
    "131...140":                        "81...",
    "141...":                           "81..."
}

# --[ plot parameters
PLOT_TITLE = "Metsamaa pindalad enamuspuuliigi kaupa"
X_AXIS_TITLE = "Aasta"
Y_AXIS_TITLE = "pindala (tuhat ha)"
LEGEND_AGE_GROUPS_TITLE = "Vanusegrupp:"
SOURCE_ANNOTATIONS = (
    "vanusegruppide andmed: https://tableau.envir.ee/views/SMI/17Vanuseklassidaegrida?%3Aembed=y<br>"
    "analüüs: https://github.com/martroben/forest_analysis/tree/main/elf_smi/<br>"
    "skript: src/04_plot_areas_by_species.py"
    # ^ Added as annotations to the plot image
)
LEGEND_COLORSCALE = "Greys"
AREA_COLORSCALES = [
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

age_group_path = os.path.join(ROOT_DIR_PATH, AGE_GROUP_PATH)
with open(age_group_path, encoding="utf-8") as read_file:
    age_group_data = pl.read_csv(read_file)


##################
# Get areas data #
##################

# Aggregate age groups
age_group_aggregated = plot.aggregate_age_groups(age_group_data, AGE_GROUP_AGGREGATION_MAP)
area_data = plot.get_areas(age_group_aggregated)
# Sum up production and protected areas
area_data_combined = (
    area_data
    .group_by(
        col("YEAR"),
        col("DOMINANT_SPECIES")
    )
    .agg(
        # Sum all age group fields
        **{field: col(field).sum() for field in set(AGE_GROUP_AGGREGATION_MAP.values())},
        UNIT=col("UNIT").first()
    )
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
unique_age_groups = sorted(
    set(AGE_GROUP_AGGREGATION_MAP.values()),
    # Sort ascending by group start age
    key=lambda x: int(re.search(r"\d+", x).group())
)
# Maximum bar heights by species
max_areas = dict(
    age_group_data
    .group_by([
        col("DOMINANT_SPECIES"),
        col("YEAR")
    ])
    .agg(AREA=pl.col("AREA").sum())
    .group_by(col("DOMINANT_SPECIES"))
    .agg(AREA=pl.col("AREA").max())
    .iter_rows()
)


###############
# Get colours #
###############

species_colorscales = {}
for row in AREA_COLORSCALES:
    species, colorscale = row
    species_colorscales[species] = colorscale

legend_colours = plot.get_colours(
    n=len(unique_age_groups),
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
# Each age group (0...20 / 20...40 etc.) is a section in the stacked bars.
# To display legend, we add extra traces with no points on plot - just colours.
# Altogether, there is a trace for each (species, age group) combination + legend traces.

traces = []

# --[ area traces
for species in COMPARISON_SPECIES:
    species_colours = plot.get_colours(
        n=len(unique_age_groups),
        scale_name=species_colorscales[species]
    )
    age_group_colour_map = dict(zip(unique_age_groups, species_colours))

    trace_data = (
        area_data_combined
        .filter(
            col("DOMINANT_SPECIES") == species,
        )
        .to_dict(as_series=False)
    )
    for age_group in unique_age_groups:
        traces += [
            plotly.graph_objects.Bar(
                x=trace_data["YEAR"],
                y=trace_data[age_group],
                name=age_group,
                offsetgroup=species,
                marker_color=age_group_colour_map[age_group],
                showlegend=False
            )
        ]

# --[ legend traces
legend_colour_map = dict(zip(unique_age_groups, legend_colours))
for age_group in unique_age_groups:
    traces += [
        plotly.graph_objects.Bar(
            x=[None], y=[None],
            name=age_group,
            marker_color=legend_colour_map[age_group],
            showlegend=True,
            legendgroup="age_groups",
            legendgrouptitle={
                "text": LEGEND_AGE_GROUPS_TITLE,
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
    y_range=(0, max_areas[species])
)


##############
# Save plots #
##############

figure = plotly.graph_objects.Figure(
    traces,
    layout
)
filename = f'pindalade_võrdlus_{"_".join(comparison_species_translated)}.png'
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
