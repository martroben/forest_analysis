# standard
import os
import re
import sys
# external
import plotly
import polars as pl
from polars import col

# local
src_path = os.path.abspath("src") if os.path.exists("src") else os.path.abspath("elf_smi/src")
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
AGE_GROUP_PATH = f'data/clean/age_group.csv'
REGENERATION_CUTTING_PATH = f'data/clean/regeneration_cutting.csv'
PLOT_SAVE_DIR_PATH = "result"

# --[ analysis parameters
REGENERATION_CUTTING_AGE_THRESHOLD = 60
# ^ Regeneration cutting total area is subtracted proportionally from age groups above the threshold
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
PLOT_TITLE = {
    "TEXT": "Mittemajandatava ja majandatava metsamaa pindalad vanusegruppide kaupa",
    # Define parts of title string that should have different colours:
    "APPLY_PRODUCTION_COLOUR_TO": "majandatava",
    "APPLY_PROTECTED_COLOUR_TO": "Mittemajandatava"
}
REGENERATION_CUTTING_NAME = "uuendusraie"
X_AXIS_TITLE = "Aasta"
Y_AXIS_TITLE = "pindala (tuhat ha)"
LEGEND_TITLE = "Vanusegrupid:"
SOURCE = (
    "vanusegruppide andmed: https://tableau.envir.ee/views/SMI/17Vanuseklassidaegrida?%3Aembed=y<br>"
    "uuendusraie andmed: https://tableau.envir.ee/views/SMI/28Raieaegrida?%3Aembed=y<br>"
    "analüüs: https://github.com/martroben/forest_analysis/tree/main/elf_smi/<br>"
    "skript: src/02_plot_age_groups.py"
    # ^ Added as annotations to the plot image
)
REGENERATION_CUTTING_COLOUR = "#C35B00"
LEGEND_COLORSCALE = "Greys"
AREA_COLORSCALES = [
    # uses plotly colorscales: https://plotly.com/python/builtin-colorscales/
    # DOMINANT_SPECIES      # TYPE          # COLORSCALE
    ("all",                  "production",   "algae"),
    ("aspen",                "production",   "Purples"),
    ("birch",                "production",   "speed"),
    ("black alder",          "production",   "turbid"),
    ("grey alder",           "production",   "YlOrBr"),
    ("other",                "production",   "Greys"),
    ("pine",                 "production",   "amp"),
    ("spruce",               "production",   "tempo"),

    ("all",                  "protected",    "Darkmint"),
    ("aspen",                "protected",    "Darkmint"),
    ("birch",                "protected",    "Darkmint"),
    ("black alder",          "protected",    "Darkmint"),
    ("grey alder",           "protected",    "Darkmint"),
    ("other",                "protected",    "Darkmint"),
    ("pine",                 "protected",    "Darkmint"),
    ("spruce",               "protected",    "Darkmint")
]


#############
# Load data #
#############

age_group_data = pl.read_csv(os.path.join(ROOT_DIR_PATH, AGE_GROUP_PATH))
regeneration_cutting_data = pl.read_csv(os.path.join(ROOT_DIR_PATH, REGENERATION_CUTTING_PATH))


###################
# Add assumptions #
###################

# Assume all regeneration cutting is done in production forest
regeneration_cutting_default_type = (
    regeneration_cutting_data
    .with_columns(
        TYPE=pl.lit("production")
    )
)


##################
# Get areas data #
##################

# Aggregate age groups
age_group_aggregated = plot.aggregate_age_groups(age_group_data, AGE_GROUP_AGGREGATION_MAP)

age_group_adjusted = plot.subtract_regeneration_cutting(
    age_group_aggregated,
    regeneration_cutting_default_type,
    REGENERATION_CUTTING_AGE_THRESHOLD
)
area_data = plot.get_areas(age_group_adjusted)


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
unique_types = (
    area_data
    .select(col("TYPE"))
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
        col("YEAR"),
        col("TYPE")
    ])
    .agg(pl.col("AREA").sum().alias("AREA"))
    .group_by(col("DOMINANT_SPECIES"))
    .agg(pl.col("AREA").max().alias("AREA"))
    .iter_rows()
)


#####################################
# Prepare regeneration cutting data #
#####################################

regeneration_cutting_plot_data = plot.get_regeneration_cutting_plot_data(
    regeneration_cutting_default_type,
    unique_years,
    unique_types,
    unique_species
)

species_for_which_regeneration_cutting_data_is_available = (
    regeneration_cutting_plot_data
    .filter(col("AREA") != 0)
    .select(col("DOMINANT_SPECIES"))
    .unique()
    .to_series()
    .to_list()
)


###############
# Get colours #
###############

species_colorscales = {}
for row in AREA_COLORSCALES:
    species, type, colorscale = row
    if not species in species_colorscales:
        species_colorscales[species] = {}
    species_colorscales[species][type] = colorscale

legend_colours = plot.get_colours(
    n=len(unique_age_groups),
    scale_name=LEGEND_COLORSCALE
)
title_colours = {}
for species, type_colorscales in species_colorscales.items():
    if not species in title_colours:
        title_colours[species] = {}
    for type, colorscale in type_colorscales.items():
        colours = plot.get_colours(5, colorscale)
        if type.lower() == "protected":
            # Use a lighter colour for protected title word
            title_colours[species][type] = colours[2]
        else:
            title_colours[species][type] = colours[3]


##############
# Get traces #
##############

# --[ strategy
# Each species is a separate plot
# Each year (1999 / 2000 etc.) is a spearate bar on the plot.
# Each type (protected / production etc.) is a separate grouped bar under a year.
# Each age group (0...20 / 20...40 etc.) is a section in the stacked bars. If regeneration data is available, we add an extra section to the stacked bars.
# To display legend, we add extra traces with no points on plot - just colours.
# Altogether, there is a trace for each (species, type, age group) combination plus the legend traces

traces = {species: [] for species in unique_species}

# --[ area traces
for species in unique_species:
    for type in unique_types:
        # get the age group: colour dict for current type/species combination:
        species_colours = plot.get_colours(
            n=len(unique_age_groups),
            scale_name=species_colorscales[species][type]
        )
        age_group_colour_map = dict(zip(unique_age_groups, species_colours))

        one_species_one_type_data = (
            area_data
            .filter(
                col("DOMINANT_SPECIES") == species,
                col("TYPE") == type
            )
            .to_dict(as_series=False)
        )
        for age_group in unique_age_groups:
            traces[species] += [
                plotly.graph_objects.Bar(
                    x=one_species_one_type_data["YEAR"],
                    y=one_species_one_type_data[age_group],
                    name=age_group,
                    offsetgroup=type,
                    marker_color=age_group_colour_map[age_group],
                    showlegend=False
                )
            ]

# --[ regeneration cutting traces
for species in unique_species:
    for type in unique_types:
        one_species_one_type_data = (
            regeneration_cutting_plot_data
            .filter(
                col("DOMINANT_SPECIES") == species,
                col("TYPE") == type
            )
            .to_dict(as_series=False)
        )
        # If all areas are zero, don't add regeneration cutting trace for that species/type
        if species not in species_for_which_regeneration_cutting_data_is_available:
            continue

        traces[species] += [
            plotly.graph_objects.Bar(
                x=one_species_one_type_data["YEAR"],
                y=one_species_one_type_data["AREA"],
                name=REGENERATION_CUTTING_NAME,
                offsetgroup=type,
                marker_color=REGENERATION_CUTTING_COLOUR,
                showlegend=False
            )
        ]

# --[ legend traces
legend_colour_map = dict(zip(unique_age_groups, legend_colours))
for species in traces.keys():
    for age_group in unique_age_groups:
        traces[species] += [
            plotly.graph_objects.Bar(
                x=[None], y=[None],
                name=age_group,
                marker_color=legend_colour_map[age_group],
                showlegend=True
            )
        ]
    # Add regeneration cutting colour to legend only if regeneration cutting data is available for this species
    if species not in species_for_which_regeneration_cutting_data_is_available:
       continue

    traces[species] += [
        plotly.graph_objects.Bar(
            x=[None], y=[None],
            name=REGENERATION_CUTTING_NAME,
            marker_color=REGENERATION_CUTTING_COLOUR,
            showlegend=True
        )
    ]


####################
# Get plot layouts #
####################

layouts = {species: None for species in unique_species}
for species in layouts.keys():
    plot_title_text = f'{PLOT_TITLE["TEXT"]} - {TRANSLATION_MAP[species].replace("_", " ")}'
    substring_colour_map = {
        PLOT_TITLE["APPLY_PROTECTED_COLOUR_TO"]: title_colours[species]["protected"],
        PLOT_TITLE["APPLY_PRODUCTION_COLOUR_TO"]: title_colours[species]["production"]
    }
    plot_title = plot.apply_colour_to_substring(
        plot_title_text,
        substring_colour_map
    )
    layouts[species] = plot.get_layout(
        plot_title,
        X_AXIS_TITLE,
        Y_AXIS_TITLE,
        LEGEND_TITLE,
        SOURCE,
        max_y_value=max_areas[species]
    )


##############
# Save plots #
##############

for species in unique_species:
    figure = plotly.graph_objects.Figure(
        traces[species],
        layouts[species]
    )
    filename = f'metsamaa_pindala_{TRANSLATION_MAP[species]}.png'
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
