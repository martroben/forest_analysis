# standard
from enum import StrEnum
from pathlib import Path
import sys
# external
import plotly
import plotly.subplots
import polars as pl
from polars import col
# local
ROOT_DIR_PATH = Path("elf_smi")
src_path = ROOT_DIR_PATH / "elf_smi" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import plot


#########
# Input #
#########

SAVE_PATH = ROOT_DIR_PATH / "result" / "vanusepüramiid_näide.png"

PLOT_TITLE = "Vanusegruppide pindalad: näide"
X_AXIS_TITLE = "pindala (kha)"
Y_AXIS_TITLE = "vanusegrupp"
SUBPLOT1_TITLE = "<b>1</b>:  aeglane kasv | kõrge raievanus"
SUBPLOT2_TITLE = "<b>2</b>:  kiire kasv | madal raievanus"
SUBPLOT3_TITLE = "<b>1 + 2</b>:  kombineeritud"
ANNOTATIONS = "<u>github.com/martroben/forest_analysis/tree/main/elf_smi/src/09_age_pyramid_example.py</u>  |  Mart Roben CC-BY"

# Proportion of the remaining mature forest cut every year
STANDARD_ANNUAL_MATURE_CUT_PROPORTION = 0.1
# Average time between regeneration cutting and having a 1 year old forest
STANDARD_RENEWAL_DELAY_YEARS = 3
AGE_GROUP_MAP = {
    # Age group aggregations (min, max): name
    (131, float("inf")):    "131..."
}

COLORSCALE = "Greys"


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

pyramid_input1 = {
    "DOMINANT_SPECIES": "example",
    "QUALITY_CLASS": "5",
    "TOTAL_AREA": 100,
    "UNIT": "kha",
    "MATURITY_AGE": 111,
    "ANNUAL_MATURE_CUT_PROPORTION": STANDARD_ANNUAL_MATURE_CUT_PROPORTION,
    "RENEWAL_DELAY_YEARS": STANDARD_RENEWAL_DELAY_YEARS
}
pyramid_input2 = {
    "DOMINANT_SPECIES": "example",
    "QUALITY_CLASS": "1",
    "TOTAL_AREA": 100,
    "UNIT": "kha",
    "MATURITY_AGE": 41,
    "ANNUAL_MATURE_CUT_PROPORTION": STANDARD_ANNUAL_MATURE_CUT_PROPORTION,
    "RENEWAL_DELAY_YEARS": STANDARD_RENEWAL_DELAY_YEARS
}
pyramid1 = get_ideal_pyramid_areas(
    total_area=pyramid_input1["TOTAL_AREA"],
    maturity_age=pyramid_input1["MATURITY_AGE"],
    annual_mature_cut_proportion=pyramid_input1["ANNUAL_MATURE_CUT_PROPORTION"],
    renewal_delay_years=pyramid_input1["RENEWAL_DELAY_YEARS"],
    # Make sure there are at least as many age values as the input map has
    mandatory_age_to_include=min(list(AGE_GROUP_MAP.keys())[-1])
)
for record in pyramid1:
    record["DOMINANT_SPECIES"] = pyramid_input1["DOMINANT_SPECIES"]
    record["QUALITY_CLASS"] = pyramid_input1["QUALITY_CLASS"]
    record["UNIT"] = pyramid_input1["UNIT"]

pyramid2 = get_ideal_pyramid_areas(
    total_area=pyramid_input2["TOTAL_AREA"],
    maturity_age=pyramid_input2["MATURITY_AGE"],
    annual_mature_cut_proportion=pyramid_input2["ANNUAL_MATURE_CUT_PROPORTION"],
    renewal_delay_years=pyramid_input2["RENEWAL_DELAY_YEARS"],
    # Make sure there are at least as many age values as the input map has
    mandatory_age_to_include=min(list(AGE_GROUP_MAP.keys())[-1])
)
for record in pyramid2:
    record["DOMINANT_SPECIES"] = pyramid_input2["DOMINANT_SPECIES"]
    record["QUALITY_CLASS"] = pyramid_input2["QUALITY_CLASS"]
    record["UNIT"] = pyramid_input2["UNIT"]

# Get age group map
max_age = sorted(pyramid1 + pyramid2, key=lambda x: x["AGE"])[-1]["AGE"]
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
data1 = (
    pl.DataFrame(
        pyramid1,
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
data2 = (
    pl.DataFrame(
        pyramid2,
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
data3 = (
    pl.concat([
        data1,
        data2
    ])
    .group_by(
        col("AGE_GROUP"),
        col("MATURITY_CLASS")
    )
    .agg(
        AREA=col("AREA").sum(),
        UNIT=col("UNIT").first(),
        SORTING_KEY=col("AGE_GROUP").str.split("...").list.get(0).cast(pl.Int16)
    )
    .sort(col("SORTING_KEY"))
    .drop(col("SORTING_KEY"))
)


###############
# Get colours #
###############

# Offset starting colours towards darker for better contrast on plot
offset_to_darker = len(set(age_group_map.values())) // 4
colours = plot.get_colours(
    n=len(set(age_group_map.values())) + offset_to_darker,
    scale_name=COLORSCALE
)
colours = colours[offset_to_darker:]


##############
# Get traces #
##############

data_non_renewed1 = (
    data1
    .filter(col("MATURITY_CLASS") == MaturityClass.NON_RENEWED)
)
data_renewed_non_mature1 = (
    data1
    .filter(col("MATURITY_CLASS") == MaturityClass.RENEWED_NON_MATURE)
)
data_mature1 = (
    data1
    .filter(col("MATURITY_CLASS") == MaturityClass.MATURE)
)

data_non_renewed2 = (
    data2
    .filter(col("MATURITY_CLASS") == MaturityClass.NON_RENEWED)
)
data_renewed_non_mature2 = (
    data2
    .filter(col("MATURITY_CLASS") == MaturityClass.RENEWED_NON_MATURE)
)
data_mature2 = (
    data2
    .filter(col("MATURITY_CLASS") == MaturityClass.MATURE)
)

data_non_renewed3 = (
    data3
    .filter(col("MATURITY_CLASS") == MaturityClass.NON_RENEWED)
)
data_renewed_non_mature3 = (
    data3
    .filter(col("MATURITY_CLASS") == MaturityClass.RENEWED_NON_MATURE)
)
data_mature3 = (
    data3
    .filter(col("MATURITY_CLASS") == MaturityClass.MATURE)
)

traces1 = []
traces1 += [
    # non renewed
    plotly.graph_objects.Bar(
        x=data_non_renewed1["AREA"].to_list(),
        y=data_non_renewed1["AGE_GROUP"].to_list(),
        orientation="h",
        marker_line_color=colours[-1],
        marker_line_width=2,
        marker_color="white",
        showlegend=False
    )
]
for i, (area, age_group) in enumerate(zip(data_renewed_non_mature1["AREA"].to_list(), data_renewed_non_mature1["AGE_GROUP"].to_list())):
    traces1 += [
        # renewed non mature
        plotly.graph_objects.Bar(
            x=[area],
            y=[age_group],
            orientation="h",
            marker_color=colours[i],
            showlegend=False
        )
    ]
traces1 += [
    # mature
    plotly.graph_objects.Bar(
        x=data_mature1["AREA"].to_list(),
        y=data_mature1["AGE_GROUP"].to_list(),
        orientation="h",
        marker_color=colours[-1],
        showlegend=False
    )
]

traces2 = []
traces2 += [
    # non renewed
    plotly.graph_objects.Bar(
        x=data_non_renewed2["AREA"].to_list(),
        y=data_non_renewed2["AGE_GROUP"].to_list(),
        orientation="h",
        marker_line_color=colours[-1],
        marker_line_width=2,
        marker_color="white",
        showlegend=False
    )
]
for i, (area, age_group) in enumerate(zip(data_renewed_non_mature2["AREA"].to_list(), data_renewed_non_mature2["AGE_GROUP"].to_list())):
    traces2 += [
        # renewed non mature
        plotly.graph_objects.Bar(
            x=[area],
            y=[age_group],
            orientation="h",
            marker_color=colours[i],
            showlegend=False
        )
    ]
traces2 += [
    # mature
    plotly.graph_objects.Bar(
        x=data_mature2["AREA"].to_list(),
        y=data_mature2["AGE_GROUP"].to_list(),
        orientation="h",
        marker_color=colours[-1],
        showlegend=False
    )
]

traces3 = []
traces3 += [
    # non renewed
    plotly.graph_objects.Bar(
        x=data_non_renewed3["AREA"].to_list(),
        y=data_non_renewed3["AGE_GROUP"].to_list(),
        orientation="h",
        marker_line_color=colours[-1],
        marker_line_width=2,
        marker_color="white",
        showlegend=False
    )
]
for i, (area, age_group) in enumerate(zip(data_renewed_non_mature3["AREA"].to_list(), data_renewed_non_mature3["AGE_GROUP"].to_list())):
    traces3 += [
        # renewed non mature
        plotly.graph_objects.Bar(
            x=[area],
            y=[age_group],
            orientation="h",
            marker_color=colours[i],
            showlegend=False
        )
    ]
traces3 += [
    # mature
    plotly.graph_objects.Bar(
        x=data_mature3["AREA"].to_list(),
        y=data_mature3["AGE_GROUP"].to_list(),
        orientation="h",
        marker_color=colours[-1],
        showlegend=False
    )
]


##############
# Get figure #
##############

figure = plotly.subplots.make_subplots(
    rows=1,
    cols=3,
    shared_yaxes=True,
    horizontal_spacing=0.15
)

for trace in traces1:
    figure = figure.add_trace(trace, row=1, col=1)

for trace in traces2:
    figure = figure.add_trace(trace, row=1, col=2)

for trace in traces3:
    figure = figure.add_trace(trace, row=1, col=3)

figure = figure.update_layout(
    barmode="relative",
    bargroupgap=0.1,
    bargap=0.1,
    height=1440,
    width=2200,
    plot_bgcolor="white",
    title={
        "text": PLOT_TITLE,
        "font": {"size": 70},
        "x": 0.5,
        "y": 0.95,
    },
    xaxis1={
        "title": {
            "text": X_AXIS_TITLE,
            "font": {"size": 32},
            "standoff": 50
        },
        "tickfont": {"size": 24},
        "range": [
            0,
            8.5
        ]
    },
    xaxis2={
        "title": {
            "text": X_AXIS_TITLE,
            "font": {"size": 32},
            "standoff": 50
        },
        "tickfont": {"size": 24},
        "range": [
            0,
            8.5
        ]
    },
    xaxis3={
        "title": {
            "text": X_AXIS_TITLE,
            "font": {"size": 32},
            "standoff": 50
        },
        "tickfont": {"size": 24},
        "range": [
            0,
            8.5
        ]
    },
    yaxis1={
        "gridcolor": "gray",
        "tickfont": {"size": 24},
        "dtick": 10,
        "title": {
            "text": Y_AXIS_TITLE,
            "font": {"size": 40},
            "standoff": 50
        }
    },
    yaxis2={
        "gridcolor": "gray",
        "dtick": 10
    },
    yaxis3={
        "gridcolor": "gray",
        "dtick": 10
    },
    margin={
        "pad": 20,                              # Axis tick label padding
        "t": 300,
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
            "yanchor": "top",
            "x": -0.13,
            "y": -0.23,
            "showarrow": False,
            "font": {"size": 20},
            "align": "left"
        },
        # Subplot titles
        {
            "text": SUBPLOT1_TITLE,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "center",
            "yanchor": "bottom",
            "x": 0.13,
            "y": 1.05,
            "showarrow": False,
            "font": {"size": 32},
            "align": "center"
        },
        {
            "text": SUBPLOT2_TITLE,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "center",
            "yanchor": "bottom",
            "x": 0.5,
            "y": 1.05,
            "showarrow": False,
            "font": {"size": 32},
            "align": "center"
        },
        {
            "text": SUBPLOT3_TITLE,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "center",
            "yanchor": "bottom",
            "x": 0.87,
            "y": 1.05,
            "showarrow": False,
            "font": {"size": 32},
            "align": "center"
        }
    ]
)


#############
# Save plot #
#############

plotly.io.write_image(
    figure,
    SAVE_PATH,
    format="png"
)
