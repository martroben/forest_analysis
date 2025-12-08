# standard
import math
import os
from pathlib import Path
# external
import plotly
import polars as pl
from polars import col


#################
# Configuration #
#################

PLOT_SUBTITLE = "⟵ mittemajandatav mets | majandatav mets ⟶"
X_AXIS_TITLE = "pindala (kha)"
Y_AXIS_TITLE = "vanusegrupp"

AGE_GROUPS = [
    # MIN_AGE           MAX_AGE         # AGE_GROUP
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
    (131,               float("inf"),   "131....")
]

SPECIES_COLORSCALES = [
    # uses plotly colorscales: https://plotly.com/python/builtin-colorscales/
    # DOMINANT_SPECIES       # ECONOMIC_CATEGORY           # COLORSCALE
    ("all",                  "production_forest",          "algae"),
    ("aspen",                "production_forest",          "Purples"),
    ("birch",                "production_forest",          "speed"),
    ("black_alder",          "production_forest",          "turbid"),
    ("grey_alder",           "production_forest",          "YlOrBr"),
    ("other",                "production_forest",          "Greys"),
    ("pine",                 "production_forest",          "amp"),
    ("spruce",               "production_forest",          "tempo"),

    ("all",                  "protected_forest",           "Darkmint"),
    ("aspen",                "protected_forest",           "Darkmint"),
    ("birch",                "protected_forest",           "Darkmint"),
    ("black_alder",          "protected_forest",           "Darkmint"),
    ("grey_alder",           "protected_forest",           "Darkmint"),
    ("other",                "protected_forest",           "Darkmint"),
    ("pine",                 "protected_forest",           "Darkmint"),
    ("spruce",               "protected_forest",           "Darkmint")
]


################
# Manual input #
################

YEAR = 2005

ROOT_DIR_PATH = "age_pyramid"
AREA_BY_AGE_GROUP_DATA_PATH = "data/clean/area_by_age_group.csv"
OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH = "data/clean/optimal_age_pyramid_areas.csv"
SAVE_PATH = "result/kuusk/vanusepüramiid_kuusk_2005.png"

# Can be several comma separated values
# spruce, pine, birch, aspen, grey_alder, black_alder, other
SPECIES = "spruce"
PLOT_TITLE = "Vanusepüramiid 2005 - kuusk"
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
AREA_BY_AGE_GROUP_DATA_PATH = os.getenv("AREA_BY_AGE_GROUP_DATA_PATH", AREA_BY_AGE_GROUP_DATA_PATH)
OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH = os.getenv("OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH", OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH)
SAVE_PATH = os.getenv("SAVE_PATH", SAVE_PATH)

SPECIES = os.getenv("SPECIES", SPECIES)
PLOT_TITLE = os.getenv("PLOT_TITLE", PLOT_TITLE)
ANNOTATIONS = os.getenv("ANNOTATIONS", ANNOTATIONS)


################
# Parse inputs #
################

SPECIES = [species.strip(" \n") for species in SPECIES.split(",")]


#########################
# Classes and functions #
#########################

# Functions to get colorscales
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


# Functions to get ticks (to display absolute value labels)
def round_to_nice_number(x: float) -> float:
    """Round x to a nice number of the form 1, 2, or 5 times 10^n."""
    if x == 0:
        return 0.0
    
    exponent = math.floor(math.log10(x))
    order_of_magnitude = 10 ** exponent

    x_scaled = x / order_of_magnitude

    if x_scaled < 1.5:
        nice_value = 1
    elif x_scaled < 3:
        nice_value = 2
    elif x_scaled < 7:
        nice_value = 5
    else:
        nice_value = 10

    return nice_value * (10 ** exponent)


def get_tick_values(x_min: float, x_max: float)-> list[float]:
    """Generate automatic tick marks for a numeric axis."""
    target_n_ticks = 5
    
    # Ensure domain includes 0
    domain_min = min(x_min, 0)
    domain_max = max(x_max, 0)
    
    span = domain_max - domain_min
    raw_step = span / (target_n_ticks - 1)
    nice_step = round_to_nice_number(raw_step)

    # Extend range to nice multiples
    nice_min = math.floor(domain_min / nice_step) * nice_step
    nice_max = math.ceil(domain_max / nice_step) * nice_step
    
    # Generate ticks
    ticks = []
    tick = nice_min
    while tick <= nice_max:
        ticks += [tick]
        tick += nice_step

    return ticks


def get_line_for_categorical_axis(x_values: list, y_values: list, line: dict) -> list[dict]:
    """
    Get a list of line shapes to show a line on categorical axis.
    Normally plotly does not allow to draw a line on categorical axis - only dots.
    This is a workaround, using the plotly.graph_object.Figure shapes attribute.
    """
    shapes = []
    for i in range(len(x_values) - 1):
        shape = {
            "type": "line",
            "x0": x_values[i],
            "y0": y_values[i],
            "x1": x_values[i + 1],
            "y1": y_values[i + 1],
            "line": line
        }
        shapes += [shape]
    
    return shapes


#############
# Load data #
#############

area_by_age_group_data_path = Path(ROOT_DIR_PATH) / AREA_BY_AGE_GROUP_DATA_PATH
with open(area_by_age_group_data_path, encoding="utf-8") as read_file:
    area_by_age_group_data = pl.read_csv(
        read_file,
        schema=pl.Schema({
            "YEAR": pl.Int16,
            "DOMINANT_SPECIES": pl.String,
            "AGE_GROUP": pl.String,
            "ECONOMIC_CATEGORY": pl.String,
            "AREA": pl.Float64,
            "UNIT": pl.String
        })
    )

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

age_groups = pl.DataFrame(
    AGE_GROUPS,
    schema={
        "MIN_AGE": pl.Float64,
        "MAX_AGE": pl.Float64,
        "AGE_GROUP": pl.String
    },
    orient="row"
)

species_colorscales = pl.DataFrame(
    SPECIES_COLORSCALES,
    schema={
        "DOMINANT_SPECIES": pl.String,
        "ECONOMIC_CATEGORY": pl.String,
        "COLORSCALE": pl.String
    },
    orient="row"
)


###############
# Filter data #
###############

# Validate filter inputs
species_in_data = set(area_by_age_group_data["DOMINANT_SPECIES"].unique().to_list())
species_bad_inputs = set(SPECIES) - species_in_data
if species_bad_inputs:
    raise ValueError(f"SPECIES contains entries not present in the data: {sorted(species_bad_inputs)}")


# Get plot data
filter_conditions = (
    (col("YEAR") == YEAR) &
    (col("DOMINANT_SPECIES").is_in(SPECIES))
)

data_filtered = (
    area_by_age_group_data
    .filter(
        filter_conditions
    )
)

data_optimal_pyramid_filtered = (
    optimal_age_pyramid_areas_data
    .filter(
        filter_conditions,
    )
)


#########################
# Prepare data for plot #
#########################

plot_data = (
    data_filtered
    .with_columns(
        MATURITY_CLASS=pl.when(
            col("AGE_GROUP").is_in(["no_trees", "renewal_not_complete"])
        )
        .then(
            pl.lit("non_renewed")
        )
        .otherwise(
            pl.lit("renewed")
        ),
        AGE_GROUP=col("AGE_GROUP").replace({
            "no_trees": "0...0",
            "renewal_not_complete": "0...0",
            "...10": "0...10",
            "141...": "141...999"
        })
    )
    # Aggregate age groups
    .with_columns(
        MIN_AGE=col("AGE_GROUP").str.split("...").list.get(0).cast(pl.Float64),
        MAX_AGE=col("AGE_GROUP").str.split("...").list.get(1).cast(pl.Float64)
    )
    .join_where(
        age_groups,
        col("MIN_AGE_AGGREGATION_MAP") <= col("MIN_AGE"),
        col("MAX_AGE_AGGREGATION_MAP") >= col("MAX_AGE"),
        suffix="_AGGREGATION_MAP"
    )
    .group_by(
        col("YEAR"),
        col("MATURITY_CLASS"),
        col("AGE_GROUP_AGGREGATION_MAP"),
        col("ECONOMIC_CATEGORY"),
        col("UNIT")
    )
    .agg(
        AREA=col("AREA").sum()
    )
    .rename({
        "AGE_GROUP_AGGREGATION_MAP": "AGE_GROUP"
    })
    .with_columns(
        AGE_GROUP_SORT_KEY=col("AGE_GROUP").str.split("...").list.get(0).cast(pl.Int16)
    )
    .sort(
        col("AGE_GROUP_SORT_KEY")
    )
)

plot_data_production = (
    plot_data
    .filter(
        col("ECONOMIC_CATEGORY") != "protected_forest"
    )
)

plot_data_protected = (
    plot_data
    .filter(
        col("ECONOMIC_CATEGORY") == "protected_forest"
    )
    # Re-aggregate to use a single maturity class
    .group_by(
        col("YEAR"),
        col("AGE_GROUP"),
        col("AGE_GROUP_SORT_KEY"),
        col("ECONOMIC_CATEGORY"),
        col("UNIT")
    )
    .agg(
        # Negative so that the bars would be on the other side of the y-axis
        AREA=-col("AREA").sum(),
    )
    .sort(
        col("AGE_GROUP_SORT_KEY")
    )
)

plot_data_production_non_renewed = (
    plot_data_production
    .filter(
        col("MATURITY_CLASS") == "non_renewed"
    )
)

plot_data_production_renewed = (
    plot_data_production
    .filter(
        col("MATURITY_CLASS") != "non_renewed"
    )
)

plot_data_optimal_pyramid = (
    data_optimal_pyramid_filtered
    .with_columns(
        MATURITY_CLASS=col("MATURITY_CLASS").replace({
            "mature": "renewed",
            "renewed_non_mature": "renewed"
        })
    )
    .join_where(
        age_groups,
        col("MIN_AGE") <= col("AGE"),
        col("MAX_AGE") >= col("AGE"),
    )
    .group_by(
        col("YEAR"),
        col("MATURITY_CLASS"),
        col("AGE_GROUP"),
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

plot_data_optimal_pyramid_non_renewed = (
    plot_data_optimal_pyramid
    .filter(
        col("MATURITY_CLASS") == "non_renewed"
    )
)

plot_data_optimal_pyramid_renewed = (
    plot_data_optimal_pyramid
    .filter(
        col("MATURITY_CLASS") != "non_renewed"
    )
    .with_columns(
        # Add non-renewed area, because scatter traces don't get stacked like bars
        AREA=(
            pl.when(
                col("AGE_GROUP") == age_groups["AGE_GROUP"].first()
            )
            .then(
                col("AREA") + plot_data_optimal_pyramid_non_renewed["AREA"].sum()
            )
            .otherwise(
                col("AREA")
            )
        )
    )
)

# Get x axis limits
x_min = plot_data_protected["AREA"].min()

real_area_max_data = (
    plot_data
    .filter(
        col("ECONOMIC_CATEGORY") != "protected_forest"
    )
    .group_by(
        col("YEAR"),
        col("AGE_GROUP")
    )
    .agg(
        # Aggregate non-renewed and renewed areas
        AREA=col("AREA").sum()
    )
)
optimal_area_max_data = (
    plot_data_optimal_pyramid
    .group_by(
        col("YEAR"),
        col("AGE_GROUP")
    )
    .agg(
        # Aggregate non-renewed and renewed areas
        AREA=col("AREA").sum()
    )
)

x_max = max(
    real_area_max_data["AREA"].max(),
    optimal_area_max_data["AREA"].max()
)


############
# Validate #
############

# Validate plot data total
plot_total_area = plot_data["AREA"].sum()
loaded_data_total_area = (
    area_by_age_group_data
    .filter(
        filter_conditions
    )
)["AREA"].sum()

if abs(plot_total_area - loaded_data_total_area) > 0.1:
    raise ValueError("Plot data area does not match the total area in the loader data!")

# check that production total equals optimal total
if abs(data_optimal_pyramid_filtered["AREA"].sum() - plot_data_production["AREA"].sum()) > 0.01 * plot_data_production["AREA"].sum():
    raise ValueError(f'Real production area {data_optimal_pyramid_filtered["AREA"].sum()} and optimal pyramid area {plot_data_production["AREA"].sum()} don\'t match')


########################
# Get plot bar colours #
########################

if len(SPECIES) == 1:
    species = SPECIES[0]
else:
    species = "all"

production_colorscale_name: str = (
    species_colorscales
    .filter(
        (col("DOMINANT_SPECIES") == species) &
        (col("ECONOMIC_CATEGORY") == "production_forest")
    )
    .select(col("COLORSCALE"))
    .to_series()
    .first()
)
protected_colorscale_name: str = (
    species_colorscales
    .filter(
        (col("DOMINANT_SPECIES") == species) &
        (col("ECONOMIC_CATEGORY") == "protected_forest")
    )
    .select(col("COLORSCALE"))
    .to_series()
    .first()
)

n_colours = len(AGE_GROUPS)

# Offset starting colours towards darker for better contrast with non-renewed part of the bar
offset_to_darker = n_colours // 4

production_colours: list[str] = get_colours(
    n=n_colours + offset_to_darker,
    scale_name=production_colorscale_name
)[offset_to_darker:]

protected_colours: list[str] = get_colours(
    n=n_colours + offset_to_darker,
    scale_name=protected_colorscale_name
)[offset_to_darker:]


##############
# Get traces #
##############

traces = []

# Production area: non-renewed
traces += [
    plotly.graph_objects.Bar(
        name="Majandatav metsamaa: mitte uuenenud ala",
        x=plot_data_production_non_renewed["AREA"].to_list(),
        y=plot_data_production_non_renewed["AGE_GROUP"].to_list(),
        orientation="h",
        marker_line_color=production_colours[-1],
        marker_line_width=2,
        marker_color="white",
        showlegend=False
    )
]

# Production area: renewed
for data_point, colour in zip(plot_data_production_renewed.to_dicts(), production_colours):
    traces += [
        plotly.graph_objects.Bar(
            name="Majandatav metsamaa: uuenenud ala",
            x=[data_point["AREA"]],
            y=[data_point["AGE_GROUP"]],
            orientation="h",
            marker_color=colour,
            showlegend=False
        )
    ]

# Protected area
for data_point, colour in zip(plot_data_protected.to_dicts(), protected_colours):
    traces += [
        plotly.graph_objects.Bar(
            name="Mitteajandatav metsamaa: uuenenud ala",
            x=[data_point["AREA"]],
            y=[data_point["AGE_GROUP"]],
            orientation="h",
            marker_color=colour,
            showlegend=False
        )
    ]


# Optimal pyramid
traces += [
    # Non-renewed optimal area as scatter plot marker
    plotly.graph_objects.Scatter(
        x=plot_data_optimal_pyramid_non_renewed["AREA"].to_list(),
        y=plot_data_optimal_pyramid_non_renewed["AGE_GROUP"].to_list(),
        showlegend=False,
        mode="markers",
        marker={
            "symbol": "line-ns-open",
            "size": 25,
            "color": "#c6c6c6",
            "line": {
                "width": 4
            }
        }
    )
]

# Renewed optimal area as shapes to produce a line
optimal_pyramid_line = get_line_for_categorical_axis(
    x_values=plot_data_optimal_pyramid_renewed["AREA"],
    y_values=plot_data_optimal_pyramid_renewed["AGE_GROUP"],
    line={
        "color": "#c6c6c6",
        "width": 4
    }
)


# Legend traces
traces += [
    # Renewed production legend
    plotly.graph_objects.Bar(
        x=[None], y=[None],
        name="Metsaga metsamaa",
        orientation="h",
        marker_color=production_colours[len(AGE_GROUPS) // 2],
        showlegend=True,
        legendrank=1
    ),
    # Non-renewed legend
    plotly.graph_objects.Bar(
        x=[None], y=[None],
        name="Lage ja selguseta ala",
        orientation="h",
        marker_line_color=production_colours[-1],
        marker_line_width=2,
        marker_color="white",
        showlegend=True,
        legendrank=2
    ),
    # Optimal pyramid area
    plotly.graph_objects.Scatter(
        x=[None], y=[None],
        name="Optimaalne vanusepüramiid",
        orientation="h",
        mode="lines",
        line={
            "color": "#c6c6c6",
            "width": 4
        },
        showlegend=True,
        legendrank=3
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
        "tickvals": get_tick_values(x_min, x_max),
        "ticktext": [abs(x) for x in get_tick_values(x_min, x_max)],
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
        "pad": 20,                              # Axis tick label padding
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
        }
    ],
    shapes=optimal_pyramid_line
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
