# standard
import os
# external
import polars as pl
from polars import col
# local
from age_group_trends.src import clean_data
from age_group_trends.src import prepare_data
from age_group_trends.src import plot_data


#########
# Input #
#########

TREE_SPECIES = "all"    # available values: all, aspen, birch, black alder, grey alder, other, pine, spruce
PLOT_SAVE_PATH = "metsamaa_pindala_kokku.png"
PLOT_TITLE = {
    "text": "Mittemajandatava ja majandatava metsamaa pindalad vanusegruppide kaupa",
    # Define parts of title string that should have different colours:
    "apply_production_colour_to": "majandatava",
    "apply_protected_colour_to": "Mittemajandatava"
}

ROOT_DIR = "age_group_trends"

# raw data load paths
# get raw data from Estonian National Forest Inventory tableau data
# https://tableau.envir.ee/views/SMI/17Vanuseklassidaegrida?%3Aembed=y
AGE_GROUP_ALL_RAW_PATHS = [
    "data/raw/1.11.X Vanuseklassid + uuend_data_all_all.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_aspen_all.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_birch_all.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_black_alder_all.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_grey_alder_all.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_other_all.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_pine_all.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_spruce_all.csv"
]
AGE_GROUP_PRODUCTION_RAW_PATHS = [
    "data/raw/1.11.X Vanuseklassid + uuend_data_all_production.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_aspen_production.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_birch_production.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_black_alder_production.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_grey_alder_production.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_other_production.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_pine_production.csv",
    "data/raw/1.11.X Vanuseklassid + uuend_data_spruce_production.csv"
]
# https://tableau.envir.ee/views/SMI/28Raieaegrida?%3Aembed=y
REGENERATION_CUTTING_RAW_PATH = "data/raw/3.2.2.X Raiete ajalugu.csv"

# clean data save paths
AGE_GROUP_CLEAN_PATH = f'data/clean/age_group_{TREE_SPECIES}.csv'
REGENERATION_CUTTING_CLEAN_PATH = f'data/clean/regeneration_cutting_{TREE_SPECIES}.csv'

# plot data save paths
PRODUCTION_REGENERATION_CUTTING_PLOT_PATH = f'data/plot/production_regeneration_cutting_{TREE_SPECIES}.csv'
PROTECTED_REGENERATION_CUTTING_PLOT_PATH = f'data/plot/protected_regeneration_cutting_{TREE_SPECIES}.csv'
PRODUCTION_AREAS_PLOT_PATH = f'data/plot/production_areas_{TREE_SPECIES}.csv'
PROTECTED_AREAS_PLOT_PATH = f'data/plot/protected_areas_{TREE_SPECIES}.csv'

# clean parameters
TRANSLATION_MAP = {
    "Selguseta ala": "unknown",
    "Lage ala": "clearcut",
    "Kokku": "all",
    "Haab": "aspen",
    "Kask": "birch",
    "Sanglepp": "black alder",
    "Hall lepp": "grey alder",
    "Teised": "other",
    "Mänd": "pine",
    "Kuusk": "spruce"
}

# analysis parameters
IS_REGENERATION_CUTTING_DATA_AVAILABLE = TREE_SPECIES == "all"
# ^ Set to False when analysing data by tree species (because there is no regeneration cutting data by individual species).
AGE_GROUP_AGGREGATION_MAP = {
    TRANSLATION_MAP["Lage ala"]:    "0...20",
    "...10":                        "0...20",
    "11...20":                      "0...20",
    "21...30":                      "21...40",
    "31...40":                      "21...40",
    "41...50":                      "41...60",
    "51...60":                      "41...60",
    "61...70":                      "61...80",
    "71...80":                      "61...80",
    "81...90":                      "81...",
    "91...100":                     "81...",
    "101...110":                    "81...",
    "111...120":                    "81...",
    "121...130":                    "81...",
    "131...140":                    "81...",
    "141...":                       "81..."
}
REGENERATION_CUTTING_AGE_THRESHOLD = 60
# ^ Regeneration cutting total area is subtracted proportionally from age groups above the threshold

# plot parameters
X_AXIS_TITLE = "Aasta"
Y_AXIS_TITLE = "pindala (tuhat ha)"
LEGEND_TITLE = "Vanusegrupid:"
SOURCE = "source: https://github.com/martroben/forest_analysis/tree/main/age_group_trends"
REGENERATION_CUTTING_NAME = "uuendusraie"

# plot colours
# uses plotly colorscales: https://plotly.com/python/builtin-colorscales/
PRODUCTION_COLORSCALES = {
    "all":          "algae",
    "aspen":        "Purples",
    "birch":        "speed",
    "black alder":  "turbid",
    "grey alder":   "YlOrBr",
    "other":        "Greys",
    "pine":         "amp",
    "spruce":       "tempo"
}
PROTECTED_COLORSCALE = "Darkmint"
PRODUCTION_COLORSCALE = PRODUCTION_COLORSCALES[TREE_SPECIES]
LEGEND_COLORSCALE = "Greys"
REGENERATION_CUTTING_COLOUR = "#C35B00"


##############
# Clean data #
##############

if IS_REGENERATION_CUTTING_DATA_AVAILABLE:
    # Read regeneration cutting data
    regeneration_cutting_raw = pl.read_csv(
        os.path.join(ROOT_DIR, REGENERATION_CUTTING_RAW_PATH),
        encoding="utf-8",
        separator=";")

    # Clean regeneration cutting data
    regeneration_cutting_clean = clean_data.clean_regeneration_cutting_data(regeneration_cutting_raw)

    # Save regeneration cutting cleaned data
    os.makedirs(
        os.path.dirname(os.path.join(ROOT_DIR, REGENERATION_CUTTING_CLEAN_PATH)),
        exist_ok=True)

    regeneration_cutting_clean.write_csv(
        os.path.join(ROOT_DIR, REGENERATION_CUTTING_CLEAN_PATH),
        separator=","
    )

# Read age group data
age_group_all_raw = pl.concat([
    pl.read_csv(
        os.path.join(ROOT_DIR, path),
        encoding="utf-8",
        separator=";"
    )
    for path in AGE_GROUP_ALL_RAW_PATHS
])

age_group_production_raw = pl.concat([
    pl.read_csv(
        os.path.join(ROOT_DIR, path),
        encoding="utf-8",
        separator=";"
    )
    for path in AGE_GROUP_PRODUCTION_RAW_PATHS
])

# Clean age group data
age_group_all = clean_data.clean_age_group_data(age_group_all_raw, "all", TRANSLATION_MAP)
age_group_production = clean_data.clean_age_group_data(age_group_production_raw, "production", TRANSLATION_MAP)
age_group_clean = clean_data.combine_all_and_production_data(age_group_all, age_group_production)

# Save cleaned age group data
os.makedirs(
    os.path.dirname(os.path.join(ROOT_DIR, AGE_GROUP_CLEAN_PATH)),
    exist_ok=True)

age_group_clean.write_csv(
    os.path.join(ROOT_DIR, AGE_GROUP_CLEAN_PATH),
    separator=","
)


##########################################
# Prepare regeneration cutting plot data #
##########################################

if IS_REGENERATION_CUTTING_DATA_AVAILABLE:
    # Use year range from age group data
    year_min = age_group_clean["YEAR"].min()
    year_max = age_group_clean["YEAR"].max()

    # Create a dummy data frame for regeneration data of protected forest
    # Assume negligible regeneration cutting in protected forests
    protected_regeneration_cutting_raw = pl.DataFrame(
        schema={
            "YEAR": pl.Int64,
            "AREA": pl.Float64,
            "UNIT": pl.String
        }
    )
    protected_regeneration_cutting_plot = prepare_data.align_regeneration_cutting_data(
        data=protected_regeneration_cutting_raw,
        year_min=year_min,
        year_max=year_max,
        type_name="protected"
    )

    # Assume that all regeneration cutting data is for production forest
    production_regeneration_cutting_raw = regeneration_cutting_clean

    production_regeneration_cutting_plot = prepare_data.align_regeneration_cutting_data(
        data=production_regeneration_cutting_raw,
        year_min=year_min,
        year_max=year_max,
        type_name="production"
    )

    # Save prepared regeneration cutting data
    os.makedirs(
        os.path.dirname(os.path.join(ROOT_DIR, PROTECTED_REGENERATION_CUTTING_PLOT_PATH)),
        exist_ok=True
    )
    protected_regeneration_cutting_plot.write_csv(
        os.path.join(ROOT_DIR, PROTECTED_REGENERATION_CUTTING_PLOT_PATH),
        separator=","
    )

    os.makedirs(
        os.path.dirname(os.path.join(ROOT_DIR, PRODUCTION_REGENERATION_CUTTING_PLOT_PATH)),
        exist_ok=True
    )
    production_regeneration_cutting_plot.write_csv(
        os.path.join(ROOT_DIR, PRODUCTION_REGENERATION_CUTTING_PLOT_PATH),
        separator=","
    )


###########################
# Prepare areas plot data #
###########################

# Select input species
age_group_species = (
    age_group_clean
    .filter(col("DOMINANT_SPECIES") == TREE_SPECIES)
)

# Add unknown area to the age group area proportionately
age_group_known = (
    age_group_species
    .filter(col("AGE_GROUP") != "unknown")
)
age_group_unknown = (
    age_group_species
    .filter(col("AGE_GROUP") == "unknown")
)
age_group_unknown_added = prepare_data.add_unknown_data(age_group_known, age_group_unknown)

# Aggregate age groups
age_group_aggregated = prepare_data.aggregate_age_groups(age_group_unknown_added, AGE_GROUP_AGGREGATION_MAP)

# Subtract regeneration cutting data
if IS_REGENERATION_CUTTING_DATA_AVAILABLE:
    all_regeneration_cutting = pl.concat([
        protected_regeneration_cutting_plot,
        production_regeneration_cutting_plot
    ])

    age_group_areas_adjusted = prepare_data.subtract_regeneration_cutting(
        age_group_aggregated,
        all_regeneration_cutting,
        REGENERATION_CUTTING_AGE_THRESHOLD
    )
else:
    age_group_areas_adjusted = age_group_aggregated

# Get areas from age group data
protected_age_group = (
    age_group_areas_adjusted
    .filter(
        col("TYPE") == "protected"
    )
)
protected_areas_plot = prepare_data.get_areas(protected_age_group)

production_age_group = (
    age_group_areas_adjusted
    .filter(
        col("TYPE") == "production"
    )
)
production_areas_plot = prepare_data.get_areas(production_age_group)


# Save prepared regeneration cutting data
os.makedirs(
    os.path.dirname(os.path.join(ROOT_DIR, PROTECTED_AREAS_PLOT_PATH)),
    exist_ok=True
)
protected_areas_plot.write_csv(
    os.path.join(ROOT_DIR, PROTECTED_AREAS_PLOT_PATH),
    separator=","
)

os.makedirs(
    os.path.dirname(os.path.join(ROOT_DIR, PRODUCTION_AREAS_PLOT_PATH)),
    exist_ok=True
)
production_areas_plot.write_csv(
    os.path.join(ROOT_DIR, PRODUCTION_AREAS_PLOT_PATH),
    separator=","
)

###################
# Get plot traces #
###################

traces = []

non_age_group_fields = ["YEAR", "UNIT", "TYPE", "DOMINANT_SPECIES"]
age_group_names = sorted([
    name for name in set(production_areas_plot.columns + protected_areas_plot.columns) 
    if name not in non_age_group_fields
])

# Add dummy traces to display legend
legend_colours = plot_data.get_colours(len(age_group_names), LEGEND_COLORSCALE)
legend_names = age_group_names

if IS_REGENERATION_CUTTING_DATA_AVAILABLE:
    legend_colours += [REGENERATION_CUTTING_COLOUR]
    legend_names += [REGENERATION_CUTTING_NAME]

traces += plot_data.get_legend_traces(legend_names, legend_colours)


# Add protected area traces
protected_areas_dict = protected_areas_plot.to_dict(as_series=False)
# ^ Convert data frames to dicts of lists (each field name is a key and values are a list)
protected_type_name = protected_areas_dict["TYPE"][0]
protected_years = protected_areas_dict["YEAR"]
protected_areas_by_age_group = {key: value for key, value in protected_areas_dict.items() if key not in non_age_group_fields}
protected_colours = plot_data.get_colours(len(age_group_names), PROTECTED_COLORSCALE)
protected_colours_by_age_group = dict(zip(protected_areas_by_age_group.keys(), protected_colours))

traces += plot_data.get_area_traces(
    protected_type_name,
    protected_years,
    protected_areas_by_age_group,
    protected_colours_by_age_group
)


# Add production areas traces
production_areas_dict = production_areas_plot.to_dict(as_series=False)
# ^ Convert data frames to dicts of lists (each field name is a key and values are a list)
production_type_name = production_areas_dict["TYPE"][0]
production_years = production_areas_dict["YEAR"]
production_areas_by_age_group = {key: value for key, value in production_areas_dict.items() if key not in non_age_group_fields}
production_colours = plot_data.get_colours(len(age_group_names), PRODUCTION_COLORSCALE)
production_colours_by_age_group = dict(zip(production_areas_by_age_group.keys(), production_colours))

traces += plot_data.get_area_traces(
    production_type_name,
    production_years,
    production_areas_by_age_group,
    production_colours_by_age_group
)


# Add regeneration cutting traces
if IS_REGENERATION_CUTTING_DATA_AVAILABLE:
    protected_regeneration_cutting_dict = protected_regeneration_cutting_plot.to_dict(as_series=False)
    # ^ Convert data frames to dicts of lists (each field name is a key and values are a list)
    protected_regeneration_cutting_years = protected_regeneration_cutting_dict["YEAR"]
    protected_regeneration_cutting_groups = {key: value for key, value in protected_regeneration_cutting_dict.items() if key not in non_age_group_fields}
    protected_regeneration_cutting_colours = dict(zip(
        protected_regeneration_cutting_groups.keys(),
        [REGENERATION_CUTTING_COLOUR] * len(protected_regeneration_cutting_groups.keys())
    ))
    traces += plot_data.get_area_traces(
        protected_type_name,
        protected_regeneration_cutting_years,
        protected_regeneration_cutting_groups,
        protected_regeneration_cutting_colours
    )

    production_regeneration_cutting_dict = production_regeneration_cutting_plot.to_dict(as_series=False)
    # ^ Convert data frames to dicts of lists (each field name is a key and values are a list)
    production_regeneration_cutting_years = production_regeneration_cutting_dict["YEAR"]
    production_regeneration_cutting_groups = {key: value for key, value in production_regeneration_cutting_dict.items() if key not in non_age_group_fields}
    production_regeneration_cutting_colours = dict(zip(
        production_regeneration_cutting_groups.keys(),
        [REGENERATION_CUTTING_COLOUR] * len(production_regeneration_cutting_groups.keys())
    ))
    traces += plot_data.get_area_traces(
        production_type_name,
        production_regeneration_cutting_years,
        production_regeneration_cutting_groups,
        production_regeneration_cutting_colours
    )


###################
# Get plot layout #
###################

# Apply indicator colours to title string
plot_title = PLOT_TITLE["text"]

protected_colour = plot_data.get_colours(5, PROTECTED_COLORSCALE)[2]
plot_title = plot_data.apply_colour_to_substring(
    plot_title,
    PLOT_TITLE["apply_protected_colour_to"],
    protected_colour
)
production_colour = plot_data.get_colours(5, PRODUCTION_COLORSCALE)[3]
plot_title = plot_data.apply_colour_to_substring(
    plot_title,
    PLOT_TITLE["apply_production_colour_to"],
    production_colour
)

# Get layout
layout = plot_data.get_layout(
    plot_title,
    X_AXIS_TITLE,
    Y_AXIS_TITLE,
    LEGEND_TITLE,
    SOURCE
)


#############
# Save plot #
#############

figure = plot_data.get_figure(traces, layout)
plot_data.save_plot(
    figure,
    os.path.join(ROOT_DIR, PLOT_SAVE_PATH)
)

# TODO: analyse by species
# TODO: update readme (add species results)
# TODO: test full deployment
