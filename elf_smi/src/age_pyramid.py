# standard
from enum import StrEnum
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


#########
# Input #
#########

PLOT_TITLE = "Ideaalne vanusepüramiid"
X_AXIS_TITLE = "pindala (kha)"
Y_AXIS_TITLE = "vanusegrupp"
ANNOTATIONS = (
    "github.com/martroben/forest_analysis/tree/main/elf_smi/src/age_pyramid.py  |  Mart Roben CC-BY"
    # ^ Added as annotations to the plot image
)

STANDARD_ANNUAL_MATURE_CUT_PROPORTION = 0.1
STANDARD_RENEWAL_DELAY_YEARS = 3
AGE_GROUP_MAP = {
    # (0, 10):                "...10",
    # (11, 20):               "11...20",
    # (21, 30):               "21...30",
    # (31, 40):               "31...40",
    # (41, 50):               "41...50",
    # (51, 60):               "51...60",
    # (61, 70):               "61...70",
    # (71, 80):               "71...80",
    # (81, 90):               "81...90",
    # (91, 100):              "91...100",
    # (101, 110):             "101...110",
    # (111, 120):             "111...120",
    # (121, 130):             "121...130",
    (131, float("inf")):    "131..."
}

COLORSCALE = "Greys" # "algae"


#########################
# Functions and classes #
#########################

class MaturityClass(StrEnum):
    NON_RENEWED = "non_renewed"
    RENEWED_NON_MATURE = "renewed_non_mature"
    MATURE = "mature"


def get_ideal_pyramid_areas(
    total_area: float,
    maturity_age: int,
    annual_mature_cut_proportion: float,
    renewal_delay_years: int,
    mandatory_age_to_include: int = None
) -> list[dict]:
    # Don't set a 
    if not mandatory_age_to_include:
        mandatory_age_to_include = 0

    # Area if non-mature age groups are evenly distributed
    ideal_area_per_age_group = total_area / ((maturity_age - 1) + ((1 - annual_mature_cut_proportion) / annual_mature_cut_proportion) + renewal_delay_years)

    areas = []
    # Get areas where the forest is not renewed yet: clear cut + very young trees
    areas += [{
        "AGE": 0,
        "AREA": renewal_delay_years * ideal_area_per_age_group,
        "MATURITY_CLASS": MaturityClass.NON_RENEWED
    }]

    # Get renewed non-mature areas: classified as forest, but average age of trees below maturity age
    for age_group in range(1, maturity_age):
        areas += [{
            "AGE": age_group,
            "AREA": ideal_area_per_age_group,
            "MATURITY_CLASS": MaturityClass.RENEWED_NON_MATURE
        }]

    # Get mature areas: average age of trees above maturity age
    age = maturity_age
    remaining_mature_area = ideal_area_per_age_group * (1 - annual_mature_cut_proportion) / annual_mature_cut_proportion
    while remaining_mature_area > total_area * 1e-4 or age <= mandatory_age_to_include:
        area = ideal_area_per_age_group * (1 - annual_mature_cut_proportion)**(age - maturity_age + 1)
        areas += [{
            "AGE": age,
            "AREA": area,
            "MATURITY_CLASS": MaturityClass.MATURE
        }]
        remaining_mature_area -= area
        age += 1
    
    return areas


#############
# Get areas #
#############

pyramid_inputs = [
    # {
    #     "DOMINANT_SPECIES": "example",
    #     "QUALITY_CLASS": "5",
    #     "TOTAL_AREA": 100,
    #     "UNIT": "kha",
    #     "MATURITY_AGE": 111,
    #     "ANNUAL_MATURE_CUT_PROPORTION": STANDARD_ANNUAL_MATURE_CUT_PROPORTION,
    #     "RENEWAL_DELAY_YEARS": STANDARD_RENEWAL_DELAY_YEARS
    # },
    {
        "DOMINANT_SPECIES": "example",
        "QUALITY_CLASS": "1",
        "TOTAL_AREA": 100,
        "UNIT": "kha",
        "MATURITY_AGE": 41,
        "ANNUAL_MATURE_CUT_PROPORTION": STANDARD_ANNUAL_MATURE_CUT_PROPORTION,
        "RENEWAL_DELAY_YEARS": STANDARD_RENEWAL_DELAY_YEARS
    }
]

pyramids = []

for input in pyramid_inputs:
    pyramid = get_ideal_pyramid_areas(
        total_area=input["TOTAL_AREA"],
        maturity_age=input["MATURITY_AGE"],
        annual_mature_cut_proportion=input["ANNUAL_MATURE_CUT_PROPORTION"],
        renewal_delay_years=input["RENEWAL_DELAY_YEARS"],
        # Make sure there are at least as many age values as the input map has
        mandatory_age_to_include=min(list(AGE_GROUP_MAP.keys())[-1])
    )
    for record in pyramid:
        record["DOMINANT_SPECIES"] = input["DOMINANT_SPECIES"]
        record["QUALITY_CLASS"] = input["QUALITY_CLASS"]
        record["UNIT"] = input["UNIT"]

    pyramids += pyramid

# Get age group map
max_age = sorted(pyramids, key=lambda x: x["AGE"])[-1]["AGE"]
age_group_map = {age: None for age in range(max_age + 1)}
for (group_min, group_max), group in AGE_GROUP_MAP.items():
    for age, existing_value in age_group_map.items():
        if existing_value:
            continue
        if group_min <= age <= group_max:
            age_group_map[age] = str(group)

for age, existing_value in age_group_map.items():
    if not existing_value:
        age_group_map[age] = str(age)

# Get data
data = (
    pl.DataFrame(
        pyramids,
        schema={
            "AGE": pl.Int16,
            "AREA": pl.Float32,
            "MATURITY_CLASS": pl.Enum(MaturityClass),
            "DOMINANT_SPECIES": pl.String,
            "QUALITY_CLASS": pl.String,
            "UNIT": pl.String
        }
    )
    .with_columns(
        AGE_GROUP = col("AGE").cast(pl.String).replace(age_group_map)
    )
    .group_by(
        col("AGE_GROUP"),
        col("MATURITY_CLASS")
    )
    .agg(
        AREA=col("AREA").sum(),
        UNIT=col("UNIT").first(),
        SORTING_KEY=col("AGE").first()
    )
    .sort(col("SORTING_KEY"))
    .drop(col("SORTING_KEY"))
)


#############
# Get range #
#############

x_range = next(
    data
    .group_by(
        col("AGE_GROUP")
    )
    .agg(
        AREA=col("AREA").sum()
    )
    .select(
        col("AREA").max().alias("MAX_AREA"),
        col("AREA").min().alias("MIN_AREA")
    )
    .iter_rows()
)


###############
# Get colours #
###############

# Start from darker colours for better contrast of plot
offset_to_darker = len(set(age_group_map.values())) // 4
colours = plot.get_colours(
    n=len(set(age_group_map.values())) + offset_to_darker,
    scale_name=COLORSCALE
)
colours = colours[offset_to_darker:]


##############
# Get traces #
##############

data_non_renewed = (
    data
    .filter(col("MATURITY_CLASS") == MaturityClass.NON_RENEWED)
)
data_renewed_non_mature = (
    data
    .filter(col("MATURITY_CLASS") == MaturityClass.RENEWED_NON_MATURE)
)
data_mature = (
    data
    .filter(col("MATURITY_CLASS") == MaturityClass.MATURE)
)

traces = []
traces += [
    # non renewed
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
for i, (area, age_group) in enumerate(zip(data_renewed_non_mature["AREA"].to_list(), data_renewed_non_mature["AGE_GROUP"].to_list())):
    traces += [
        # renewed non mature
        plotly.graph_objects.Bar(
            x=[area],
            y=[age_group],
            orientation="h",
            marker_color=colours[i],
            showlegend=False
        )
    ]
traces += [
    # mature
    plotly.graph_objects.Bar(
        x=data_mature["AREA"].to_list(),
        y=data_mature["AGE_GROUP"].to_list(),
        orientation="h",
        marker_color=colours[-1],
        showlegend=False
    )
]


##############
# Get layout #
##############

layout = plotly.graph_objects.Layout(
    barmode="relative",
    bargroupgap=0.1,
    bargap=0.1,
    height=1440,
    width=1000,
    plot_bgcolor="white",
    title={
        "text": PLOT_TITLE,
        "font": {"size": 70},
        "x": 0.5,
        "y": 0.95,
    },
    xaxis={
        "title": {
            "text": X_AXIS_TITLE,
            "font": {"size": 40},
            "standoff": 50
        },
        "tickfont": {"size": 24},
        # "range": [
        #     min(range),
        #     max(range)
        # ]
    },
    yaxis={
        "gridcolor": "gray",
        "tickfont": {"size": 24},
        "dtick": 10,
        "title": {
            "text": Y_AXIS_TITLE,
            "font": {"size": 40},
            "standoff": 50
        }
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
            "text": ANNOTATIONS,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "left",
            "yanchor": "bottom",
            "x": -0.4,
            "y": -0.25,
            "showarrow": False,
            "font": {"size": 20},
            "align": "left"
        }
    ]
)


#############
# Save plot #
#############

figure = plotly.graph_objects.Figure(
    traces,
    layout
)

save_path = "/home/mart/Python/forest_analysis/elf_smi/data/_test/test.png"

plotly.io.write_image(
    figure,
    save_path,
    format="png"
)
