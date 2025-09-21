# standard
import datetime
import os
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

# --[ plot parameters
PLOT_TITLE = "Metsamaa pindalad enamuspuuliigi kaupa"
X_AXIS_TITLE = "Aasta"
Y_AXIS_TITLE = "pindala (tuhat ha)"
LEGEND_TITLE = "Puuliik:"
SOURCE_ANNOTATIONS = (
    "1999 ja hilisemad andmed: https://tableau.envir.ee/views/SMI/17Vanuseklassidaegrida?%3Aembed=y<br>"
    "varasemad andmed: https://keskkonnaportaal.ee/sites/default/files/Teemad/Mets/Mets2021.pdf#page=42<br>"
    "analüüs: https://github.com/martroben/forest_analysis/tree/main/elf_smi/<br>"
    "skript: src/05_plot_species_area_comparison.py"
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
MANUAL_DATA_POINTS = [
    # YEAR      # DOMINANT_SPECIES      # AREA
    (1958,      "pine",                 594.8),
    (1958,      "birch",                386.1),
    (1975,      "pine",                 721.5),
    (1975,      "birch",                506.5),
    (1988,      "pine",                 749.6),
    (1988,      "birch",                540.4)
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

manual_area_data = (
    pl.from_records(
        MANUAL_DATA_POINTS,
        schema={
            "YEAR": pl.Int64,
            "DOMINANT_SPECIES": pl.String,
            "AREA": pl.Float64
        }
    )
    .with_columns(
        UNIT=pl.lit("kha")
    )
)
loaded_area_data = (
    age_group_data
    .group_by(
        col("YEAR"),
        col("DOMINANT_SPECIES")
    )
    .agg(
        AREA=col("AREA").sum(),
        UNIT=col("UNIT").first()
    )
)
area_data = (
    pl.concat([
        manual_area_data,
        loaded_area_data
    ])
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
# Maximum bar heights by species
max_areas = dict(
    age_group_data
    .group_by(
        col("YEAR"),
        col("DOMINANT_SPECIES")
    )
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

title_colours = {}
for species, colorscale in species_colorscales.items():
    colours = plot.get_colours(5, colorscale)
    title_colours[species] = colours[3]

legend_colours = title_colours


##############
# Get traces #
##############

# --[ strategy
# Each year (1999 / 2000 etc.) is a separate group of bars on the plot.
# Each selected species (pine, birch etc.) is a separate grouped bar under a year.
# To display legend, we add extra traces with no points on plot - just colours.
# Altogether, there is a trace for each species + legend traces.

traces = []

# --[ area traces
for species in COMPARISON_SPECIES:
    trace_data = (
        area_data
        .filter(
            col("DOMINANT_SPECIES") == species,
        )
        .to_dict(as_series=False)
    )

    # Convert x values to dates
    offset_days = 60
    x_dates = []
    for year in trace_data["YEAR"]:
        x_date = datetime.datetime.strptime(str(year), "%Y")
        # Apply offset to center the x-axis labels to the bars
        x_date_with_offset = x_date + datetime.timedelta(days=offset_days)
        x_dates += [x_date_with_offset]

    traces += [
        plotly.graph_objects.Bar(
            x=x_dates,
            y=trace_data["AREA"],
            name=TRANSLATION_MAP[species],
            offsetgroup=species,
            marker_color=legend_colours[species],
            showlegend=False
        )
    ]

# --[ legend traces
for species in reversed(COMPARISON_SPECIES):
    #          ^ Reverse so that items on legend would appear in the correct order (legend is populated from bottom up)
    traces += [
        plotly.graph_objects.Bar(
            x=[None], y=[None],
            name=TRANSLATION_MAP[species],
            marker_color=legend_colours[species],
            showlegend=True,
            legendgroup="species",
            legendgrouptitle={
                "text": LEGEND_TITLE,
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
layout = plot.get_layout_date_axis(
    title=plot_title,
    x_axis_title=X_AXIS_TITLE,
    y_axis_title=Y_AXIS_TITLE,
    source_annotations=SOURCE_ANNOTATIONS,
    x_values=unique_years,
    y_range=(0, max_areas[species])
)


##############
# Save plots #
##############

figure = plotly.graph_objects.Figure(
    traces,
    layout
)
filename = f'puuliikide_pindala_ajalugu_{"_".join(comparison_species_translated)}.png'
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
