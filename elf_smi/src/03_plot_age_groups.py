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
REGENERATION_CUTTING_PATH = "data/clean/regeneration_cutting.csv"
CUTTING_AGE_PATH = "data/clean/cutting_age.csv"
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
LEGEND_AGE_GROUPS_TITLE = "Vanusegrupp:"
LEGEND_TARGETS_TITLE = "Sihtmäär:"
SOURCE_ANNOTATIONS = (
    "vanusegruppide andmed: https://tableau.envir.ee/views/SMI/17Vanuseklassidaegrida?%3Aembed=y<br>"
    "uuendusraie andmed: https://tableau.envir.ee/views/SMI/28Raieaegrida?%3Aembed=y<br>"
    "analüüs: https://github.com/martroben/forest_analysis/tree/main/elf_smi/<br>"
    "skript: src/03_plot_age_groups.py"
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

age_group_path = os.path.join(ROOT_DIR_PATH, AGE_GROUP_PATH)
with open(age_group_path, encoding="utf-8") as read_file:
    age_group_data = pl.read_csv(read_file)

regeneration_cutting_path = os.path.join(ROOT_DIR_PATH, REGENERATION_CUTTING_PATH)
with open(regeneration_cutting_path, encoding="utf-8") as read_file:
    regeneration_cutting_data = pl.read_csv(read_file)

cutting_age_path = os.path.join(ROOT_DIR_PATH, CUTTING_AGE_PATH)
with open(cutting_age_path, encoding="utf-8") as read_file:
    cutting_age_data = pl.read_csv(read_file)


#####################
# Apply assumptions #
#####################

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
    cutting_age_data
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
    .agg(AREA=col("AREA").sum())
    .group_by(col("DOMINANT_SPECIES"))
    .agg(AREA=col("AREA").max())
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


#########################################
# Get target areas for lowest age group #
#########################################

target_areas_up_to_20_years = plot.get_target_area_up_to_k_years(
    age_group_data,
    cutting_age_data,
    k_years=20
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

target_colours = {}
for species, type_colorscales in species_colorscales.items():
    colours = plot.get_colours(
        n=len(unique_age_groups),
        scale_name=type_colorscales["production"]
    )
    target_colours[species] = colours[3]
    #                                 ^ Use colour from a slightly older age group

title_colours = {}
for species, type_colorscales in species_colorscales.items():
    if not species in title_colours:
        title_colours[species] = {}
    for type, colorscale in type_colorscales.items():
        colours = plot.get_colours(5, colorscale)
        if type.lower() == "protected":
            title_colours[species][type] = colours[2]
            #                                      ^ Use a lighter colour fto get a better contrast between protected and production
        else:
            title_colours[species][type] = colours[3]


##############
# Get traces #
##############

# --[ strategy
# Each species is a separate plot
# Each year (1999 / 2000 etc.) is a separate group of bars on the plot.
# Each type (protected / production etc.) is a separate grouped bar under a year.
# Each age group (0...20 / 20...40 etc.) is a section in the stacked bars. If regeneration data is available, we add an extra section to the stacked bars.
# In addition we add the lowest age group target area marker traces for each year.
# To display legend, we add extra traces with no points on plot - just colours.
# Altogether, there is a trace for each (species, type, age group) combination + legend traces + target area marker traces.

traces = {species: [] for species in unique_species}

# --[ area traces
unique_types_sorted = sorted(unique_types, key=lambda x: {"protected": 1, "production": 2}.get(x, 3))
# ^ Make sure protected type is before production in the graph
for species in unique_species:
    for type in unique_types_sorted:
        # get the age group: colour dict for current type/species combination:
        species_colours = plot.get_colours(
            n=len(unique_age_groups),
            scale_name=species_colorscales[species][type]
        )
        age_group_colour_map = dict(zip(unique_age_groups, species_colours))

        trace_data = (
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
                    x=trace_data["YEAR"],
                    y=trace_data[age_group],
                    name=age_group,
                    offsetgroup=type,
                    marker_color=age_group_colour_map[age_group],
                    showlegend=False
                )
            ]

# --[ regeneration cutting traces
for species in unique_species:
    for type in unique_types:
        trace_data = (
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
                x=trace_data["YEAR"],
                y=trace_data["AREA"],
                name=REGENERATION_CUTTING_NAME,
                offsetgroup=type,
                marker_color=REGENERATION_CUTTING_COLOUR,
                showlegend=False
            )
        ]

# --[ target traces
for species in unique_species:
    for type in unique_types:
        trace_data = (
            target_areas_up_to_20_years
            .filter(
                col("DOMINANT_SPECIES") == species,
                col("TYPE") == type
            )
            .to_dict(as_series=False)
        )
        # Skip species / types where there aren't a single value
        if not any(trace_data["TARGET_AREA"]):
            continue

        species_colours = plot.get_colours(
            n=len(unique_age_groups),
            scale_name=species_colorscales[species][type]
        )
        traces[species] += [
            plot.get_horizontal_segments_trace(
                x=trace_data["YEAR"],
                y=trace_data["TARGET_AREA"],
                colour=species_colours[2]
                #                      ^ Use colour from a slightly older age group
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
                showlegend=True,
                legendgroup="age_groups",
                legendgrouptitle={
                    "text": LEGEND_AGE_GROUPS_TITLE,
                    "font": {"size": 28}
                }
            )
        ]
    # Add regeneration cutting colour to legend only if regeneration cutting data is available for this species
    if species in species_for_which_regeneration_cutting_data_is_available:
        traces[species] += [
            plotly.graph_objects.Bar(
                x=[None], y=[None],
                name=REGENERATION_CUTTING_NAME,
                marker_color=REGENERATION_CUTTING_COLOUR,
                showlegend=True,
                legendgroup="age_groups",
                legendgrouptitle={
                    "text": LEGEND_AGE_GROUPS_TITLE,
                    "font": {"size": 28}
                }
            )
        ]
    # Add age group area target legends
    traces[species] += [
        plotly.graph_objects.Scatter(
            x=[None], y=[None],
            name="0...20",
            marker_color=target_colours[species],
            line_width=4,
            mode="lines",
            showlegend=True,
            legendgroup="targets",
            legendgrouptitle={
                "text": f'<br><br>{LEGEND_TARGETS_TITLE}',
                "font": {"size": 28}
            }
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
