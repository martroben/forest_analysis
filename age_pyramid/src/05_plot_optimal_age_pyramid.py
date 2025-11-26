# standard
import os
from pathlib import Path
# external
import plotly
import polars as pl
from polars import col


#################
# Configuration #
#################

AGE_GROUPS = [
    # MIN_AGE           # MAX_AGE       # AGE_GROUP
    (0,                 10,             "0...10"),
    (11,                20,             "11...20"),
    (21,                30,             "21...30"),
    (31,                40,             "31...40"),
    (41,                50,             "41...50"),
    (51,                60,             "51...60"),
    (61,                70,             "61...70"),
    (71,                80,             "71...80"),
    (81,                90,             "81...90"),
    (91,                100,            "91...100"),
    (101,               110,            "101...110"),
    (111,               120,            "111...120"),
    (121,               130,            "121...130"),
    (131,               140,            "131...140"),
    (141,               150,            "141...150"),
    (151,               float("inf"),   "151...")
]

COLORSCALE = "Greys"

PLOT_TITLE = "Optimaalne vanusepüramiid"
X_AXIS_TITLE = "pindala (kha)"
Y_AXIS_TITLE = "vanusegrupp"


################
# Manual input #
################

YEAR = 2024
ROOT_DIR_PATH = "age_pyramid"
OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH = "data/clean/optimal_age_pyramid_areas.csv"
AREA_BY_QUALITY_CLASS_DATA_PATH = "data/clean/area_by_quality_class.csv"
SAVE_PATH = "result/optimaalne/optimaalne_vanusepüramiid_haab_IA.png"

# spruce, pine, birch, aspen, grey_alder, black_alder, other
SPECIES = "aspen"
# 5A-5B, 5, 4, 3, 2, 1A, 1
QUALITY_CLASSES = "1A"
# state_forest_management_centre, other
MANAGED_BY = "state_forest_management_centre, other"

PLOT_SUBTITLE = "Haab IA | kiire kasv, madal raievanus"
ANNOTATIONS = (
    "<u>github.com/martroben/forest_analysis/tree/main/age_pyramid/</u>"
    "<br>"
    "CC-BY license: Mart Roben"
)

#############
# Env input #
#############

# Manual inputs act as defaults and can be overridden by env inputs

YEAR = int(os.getenv("YEAR", YEAR))
ROOT_DIR_PATH = os.getenv("ROOT_DIR_PATH", ROOT_DIR_PATH)
OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH = os.getenv("OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH", OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH)
AREA_BY_QUALITY_CLASS_DATA_PATH = os.getenv("AREA_BY_QUALITY_CLASS_DATA_PATH", AREA_BY_QUALITY_CLASS_DATA_PATH)
SAVE_PATH = os.getenv("SAVE_PATH", SAVE_PATH)

SPECIES = os.getenv("SPECIES", SPECIES)
QUALITY_CLASSES = os.getenv("QUALITY_CLASSES", QUALITY_CLASSES)
MANAGED_BY = os.getenv("MANAGED_BY", MANAGED_BY)

PLOT_SUBTITLE = os.getenv("PLOT_SUBTITLE", PLOT_SUBTITLE)
ANNOTATIONS = os.getenv("ANNOTATIONS", ANNOTATIONS)


################
# Parse inputs #
################

SPECIES = [s.strip() for s in SPECIES.split(",") if s.strip()]
QUALITY_CLASSES = [s.strip() for s in QUALITY_CLASSES.split(",") if s.strip()]
MANAGED_BY = [s.strip() for s in MANAGED_BY.split(",") if s.strip()]


#########################
# Classes and functions #
#########################

def rgb_to_hex(rgb: str) -> str:
    """
    Convert string in the form of 'rgb(10, 20, 30)' to a hex string.
    """
    rgb_components = [int(x.strip()) for x in rgb.strip("rgb()").split(",")]
    hex = "#{0:02x}{1:02x}{2:02x}".format(*rgb_components)
    return hex


def get_colorscale_positions(n: int) -> list[float]:
    """
    Get n evenly spaced numbers between 1/n and 1.
    Used to get colorscale values.
    """
    return [i / n for i in range(1, n + 1)]


def get_colours(n: int, scale_name: str) -> list[str]:
    """
    Get n evenly spaced colours from a plotly colorscale.
    """
    scale_positions = get_colorscale_positions(n)

    colours_rgb = plotly.colors.sample_colorscale(
        scale_name,
        scale_positions
    )
    colours_hex = [rgb_to_hex(colour) for colour in colours_rgb]

    return colours_hex


#############
# Load data #
#############

optimal_age_pyramid_areas_data_path = Path(ROOT_DIR_PATH) / OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH
with open(optimal_age_pyramid_areas_data_path, encoding="utf-8") as read_file:
    optimal_age_pyramid_areas_data = pl.read_csv(
        read_file,
        schema=pl.Schema({
            "YEAR": pl.Int16,
            "MANAGED_BY": pl.String,
            "DOMINANT_SPECIES": pl.String,
            "QUALITY_CLASS": pl.String,
            "AGE": pl.Float64,
            "AREA": pl.Float64,
            "UNIT": pl.String,
            "MATURITY_CLASS": pl.String,
            "ANNUAL_MATURE_CUT_PROPORTION": pl.Float64,
            "NON_RENEWED_PROPORTION": pl.Float64
        })
    )

area_by_quality_class_data_path = Path(ROOT_DIR_PATH) / AREA_BY_QUALITY_CLASS_DATA_PATH
with open(area_by_quality_class_data_path, encoding="utf-8") as read_file:
    area_by_quality_class_data = pl.read_csv(read_file)

age_groups = pl.DataFrame(
    AGE_GROUPS,
    schema={
        "MIN_AGE": pl.Float64,
        "MAX_AGE": pl.Float64,
        "AGE_GROUP": pl.String
    },
    orient="row"
)

#########################
# Prepare data for plot #
#########################

# Validate filter inputs
species_in_data = set(optimal_age_pyramid_areas_data["DOMINANT_SPECIES"].unique().to_list())
species_bad_inputs = set(SPECIES) - species_in_data
if species_bad_inputs:
    raise ValueError(f"SPECIES contains entries not present in the data: {sorted(species_bad_inputs)}")

quality_classes_in_data = set(optimal_age_pyramid_areas_data["QUALITY_CLASS"].unique().to_list())
quality_classes_bad_inputs = set(QUALITY_CLASSES) - quality_classes_in_data
if quality_classes_bad_inputs:
    raise ValueError(f"QUALITY_CLASSES contains entries not present in the data: {sorted(quality_classes_bad_inputs)}")

managed_by_in_data = set(optimal_age_pyramid_areas_data["MANAGED_BY"].unique().to_list())
managed_by_bad_inputs = set(MANAGED_BY) - managed_by_in_data
if managed_by_bad_inputs:
    raise ValueError(f"MANAGED_BY contains entries not present in the data: {sorted(managed_by_bad_inputs)}")

# Get plot data
filter_conditions = (
    (col("YEAR") == YEAR) &
    (col("DOMINANT_SPECIES").is_in(SPECIES)) &
    (col("QUALITY_CLASS").is_in(QUALITY_CLASSES)) &
    (col("MANAGED_BY").is_in(MANAGED_BY))
)

plot_data = (
    optimal_age_pyramid_areas_data
    .filter(
        filter_conditions
    )
    .join_where(
        age_groups,
        col("MIN_AGE") <= col("AGE"),
        col("MAX_AGE") >= col("AGE")
    )
    # Aggregate age groups
    .group_by(
        col("AGE_GROUP"),
        col("MATURITY_CLASS"),
        col("UNIT")
    )
    .agg(
        AREA=col("AREA").sum()
    )
    .with_columns(
        AGE_GROUP_SORT_KEY=col("AGE_GROUP").str.split("...").list.get(0).cast(pl.Int16)
    )
    .sort(
        col("AGE_GROUP_SORT_KEY")
    )
)


########################
# Get plot bar colours #
########################

# Offset starting colours towards darker for better contrast on plot
offset_to_darker = len(AGE_GROUPS) // 4
# Create a divide between non mature age groups and mature age group colour
max_age_offset = len(AGE_GROUPS) // 3

colours = get_colours(
    n=len(AGE_GROUPS) + offset_to_darker + max_age_offset,
    scale_name=COLORSCALE
)
colours = colours[offset_to_darker:]


###################
# Get plot traces #
###################

# Traces = bars in the horizontal bar plot
# For stacked bars, each stacked element is a separate trace
traces = []

# Non-renewed
data_non_renewed = (
    plot_data
    .filter(
        col("MATURITY_CLASS") == "non_renewed"
    )
)
traces += [
    plotly.graph_objects.Bar(
        x=data_non_renewed["AREA"].to_list(),
        y=data_non_renewed["AGE_GROUP"].to_list(),
        orientation="h",
        marker_line_color=colours[-1],
        marker_line_width=2,
        marker_color="white",
        showlegend=False
    )
]

# Renewed non-mature
data_renewed_non_mature = (
    plot_data
    .filter(
        col("MATURITY_CLASS") == "renewed_non_mature"
    )
)
for i, (area, age_group) in enumerate(zip(data_renewed_non_mature["AREA"].to_list(), data_renewed_non_mature["AGE_GROUP"].to_list())):
    traces += [
        plotly.graph_objects.Bar(
            x=[area],
            y=[age_group],
            orientation="h",
            marker_color=colours[i],
            showlegend=False
        )
    ]

# Mature
data_mature = (
    plot_data
    .filter(
        col("MATURITY_CLASS") == "mature"
    )
)
for i, (area, age_group) in enumerate(zip(data_mature["AREA"].to_list(), data_mature["AGE_GROUP"].to_list())):
    traces += [
        plotly.graph_objects.Bar(
            x=[area],
            y=[age_group],
            orientation="h",
            marker_color=colours[-1],
            showlegend=False
        )
    ]

# Legend entries
traces += [
    # Non-renewed legend
    plotly.graph_objects.Bar(
        x=[None], y=[None],
        name="Mitte uuenenud ala",
        orientation="h",
        marker_line_color=colours[-1],
        marker_line_width=2,
        marker_color="white",
        showlegend=True
    )
]

traces += [
    # Renewed non-mature legend
    plotly.graph_objects.Bar(
        x=[None], y=[None],
        name="Mitte raieküps mets",
        orientation="h",
        marker_color=colours[len(AGE_GROUPS) // 2],
        showlegend=True
    )
]

traces += [
    # Mature legend
    plotly.graph_objects.Bar(
        x=[None], y=[None],
        name="Raieküps mets",
        orientation="h",
        marker_color=colours[-1],
        showlegend=True
    )
]


##############
# Get layout #
##############

layout = plotly.graph_objects.Layout(
    barmode="relative",
    bargroupgap=0.1,
    bargap=0.1,
    height=1500,
    width=1500,
    plot_bgcolor="white",
    title={
        "text": ANNOTATIONS,
        "font": {"size": 24},
        "yanchor": "top",
        "xanchor": "left",
        "x": 0.01,
        "y": 0.03,
    },
    xaxis={
        "title": {
            "text": X_AXIS_TITLE,
            "font": {"size": 35},
            "standoff": 50
        },
        "tickfont": {"size": 24}
    },
    yaxis={
        "tickfont": {"size": 24},
        "title": {
            "text": Y_AXIS_TITLE,
            "font": {"size": 35},
            "standoff": 50
        }
    },
    legend={
        "font": {"size": 35},
        "yanchor": "top",
        "xanchor": "right",
        "y": 0.95,
        "x": 0.99
    },
    margin={
        "pad": 20,          # Axis tick label padding
        "t": 250,
        "b": 250,
        "l": 250,
        "r": 200
    },
    annotations=[
        {
            "text": PLOT_TITLE,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "center",
            "yanchor": "bottom",
            "x": 0.5,
            "y": 1.11,
            "showarrow": False,
            "font": {"size": 60},
            "align": "center"
        },
        {
            "text": PLOT_SUBTITLE,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "center",
            "yanchor": "bottom",
            "x": 0.5,
            "y": 1.07,
            "showarrow": False,
            "font": {"size": 32},
            "align": "center"
        },
    ]
)


#############
# Save plot #
#############

figure = plotly.graph_objects.Figure(
    traces,
    layout
)

save_path = Path(ROOT_DIR_PATH) / SAVE_PATH
save_path.parent.mkdir(parents=True, exist_ok=True)
plotly.io.write_image(
    figure,
    save_path,
    format="png"
)
