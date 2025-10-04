# standard
from enum import StrEnum
from pathlib import Path
import sys
# external
import plotly
import polars as pl
from polars import col
# local
ROOT_DIR_PATH = Path("elf_smi")

src_path = ROOT_DIR_PATH / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import plot


#########
# Input #
#########

QUALITY_CLASS_DATA_PATH = ROOT_DIR_PATH / "data" / "clean" / "quality_class.csv"
SAVE_PATH = ROOT_DIR_PATH / "result" / "vanusepüramiid_kokku.png"
YEAR = 2024

PLOT_TITLE = "Vanusegruppide pindalad"
PLOT_SUBTITLE = "optimaalne jaotus ühtlase raiemahu hoidmiseks"
X_AXIS_TITLE = "pindala (kha)"
Y_AXIS_TITLE = "vanusegrupp"
ANNOTATIONS = (
    "<u>github.com/martroben/forest_analysis/tree/main/elf_smi/src/10_age_pyramid_all.py</u>"
    "<br>"
    "Mart Roben CC-BY"
)

# Proportion of the remaining mature forest cut every year
STANDARD_ANNUAL_MATURE_CUT_PROPORTION = 0.05
# Average time between regeneration cutting and having a 1 year old forest
STANDARD_RENEWAL_DELAY_YEARS = 3

# Age group aggregations (min, max): name
AGE_GROUP_MAP = {
    # Aggregate maximum age group (also sets y max)
    (0, 10):                "0...10",
    (11, 20):               "11...20",
    (21, 30):               "21...30",
    (31, 40):               "31...40",
    (41, 50):               "41...50",
    (51, 60):               "51...60",
    (61, 70):               "61...70",
    (71, 80):               "71...80",
    (81, 90):               "81...90",
    (91, 100):              "91...100",
    (101, 110):             "101...110",
    (111, 120):             "111...120",
    (121, 130):             "121...130",
    (131, float("inf")):    "131..."
}

COLORSCALE = "Greys"


#################
# Maturity ages #
#################

# https://www.riigiteataja.ee/akt/126022014017?leiaKehtiv §3 pt.1^2
MATURITY_AGES = [
    # SPECIES       # QUALITY_CLASS     # MATURITY_AGE
    ("pine",        "1A",               90),
    ("pine",        "1",                90),
    ("pine",        "2",                90),
    ("pine",        "3",               100),
    ("pine",        "4",               110),
    ("pine",        "5",               120),
    ("pine",        "5A",              120),
    ("spruce",      "1A",               60),
    ("spruce",      "1",                70),
    ("spruce",      "2",                80),
    ("spruce",      "3",                90),
    ("spruce",      "4",                90),
    ("spruce",      "5",                90),
    ("spruce",      "5A",               90),
    ("birch",       "1A",               60),
    ("birch",       "1",                60),
    ("birch",       "2",                70),
    ("birch",       "3",                70),
    ("birch",       "4",                70),
    ("birch",       "5",                70),
    ("birch",       "5A",               70),
    ("aspen",       "1A",               30),
    ("aspen",       "1",                40),
    ("aspen",       "2",                40),
    ("aspen",       "3",                50),
    ("aspen",       "4",                50),
    ("black alder", "1A",               60),
    ("black alder", "1",                60),
    ("black alder", "2",                60),
    ("black alder", "3",                60),
    ("black alder", "4",                60),
    ("black alder", "5",                60),
    ("black alder", "5A",               60),
    ("hardwood",    "1A",               90),
    ("hardwood",    "1",                90),
    ("hardwood",    "2",               100),
    ("hardwood",    "3",               110),
    ("hardwood",    "4",               120),
    ("hardwood",    "5",               130),
    ("hardwood",    "5A",              130)
]


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
    dominant_species: str,
    quality_class: str,
    minimum_top_age: int = None
) -> list[dict]:
    # Don't set a minimum top age group
    if not minimum_top_age:
        minimum_top_age = 0

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
    while remaining_mature_area > total_area * 1e-4 or age <= minimum_top_age:
        area = ideal_area_per_age_group * (1 - annual_mature_cut_proportion)**(age - maturity_age + 1)
        areas += [{
            "AGE": age,
            "AREA": area,
            "MATURITY_CLASS": MaturityClass.MATURE
        }]
        remaining_mature_area -= area
        age += 1
    
    for record in areas:
        record["DOMINANT_SPECIES"] = dominant_species
        record["QUALITY_CLASS"] = quality_class

    return areas


#############
# Load data #
#############

with open(QUALITY_CLASS_DATA_PATH, encoding="utf-8") as read_file:
    quality_class_data = pl.read_csv(read_file)


#############
# Get areas #
#############

maturity_ages_data = (
    pl.DataFrame(
        MATURITY_AGES,
        schema={
            "SPECIES": pl.String,
            "QUALITY_CLASS": pl.String,
            "MATURITY_AGE": pl.Int16
        },
        orient="row"
    )
    .with_columns(
        # Assume that anything designated as "other" species has the same maturity age as hardwood
        SPECIES=pl.when(
            col("SPECIES").str.to_lowercase() == "hardwood"
        ).then(
            pl.lit("other")
        ).otherwise(
            col("SPECIES")
        ),
        # Assume that quality class 5B has the same maturity class as 5A
        QUALITY_CLASS=pl.when(
            col("QUALITY_CLASS") == "5A"
        ).then(
            pl.lit("5A-5B")
        ).otherwise(
            col("QUALITY_CLASS")
        )
    )
)

species_quality_classes = (
    quality_class_data
    .filter(
        col("YEAR") == YEAR,
        col("OWNER").str.to_lowercase() == "all",
        col("TYPE").str.to_lowercase() == "production",
        col("QUALITY_CLASS").str.to_lowercase() != "all",
        col("AREA").is_not_null()
    )
    .join(
        maturity_ages_data,
        how="left",
        left_on=[col("DOMINANT_SPECIES"), col("QUALITY_CLASS")],
        right_on=[col("SPECIES"), col("QUALITY_CLASS")]
    )
    .with_columns(
        # Assign maturity age 30 to grey alder
        # Assign maturity age 50 to aspen with quality class "5"
        MATURITY_AGE=pl.when(
            col("DOMINANT_SPECIES").str.to_lowercase() == "grey alder"
        ).then(
            pl.lit(30)
        ).when(
            (col("DOMINANT_SPECIES").str.to_lowercase() == "aspen") &
            (col("QUALITY_CLASS") == "5")
        ).then(
            pl.lit(50)
        ).otherwise(
            col("MATURITY_AGE")
        )
    )
    .to_dicts()
)

pyramids = []
for species_quality_class in species_quality_classes:
    pyramids += get_ideal_pyramid_areas(
        total_area=species_quality_class["AREA"],
        maturity_age=species_quality_class["MATURITY_AGE"],
        annual_mature_cut_proportion=STANDARD_ANNUAL_MATURE_CUT_PROPORTION,
        renewal_delay_years=STANDARD_RENEWAL_DELAY_YEARS,
        dominant_species=species_quality_class["DOMINANT_SPECIES"],
        quality_class=species_quality_class["QUALITY_CLASS"],
        # Make sure there are at least as many age values as the input map has
        minimum_top_age=min(list(AGE_GROUP_MAP.keys())[-1])
    )

# Get age group map
max_age = sorted(pyramids, key=lambda x: x["AGE"])[-1]["AGE"]
age_group_map = {age: None for age in range(max_age + 1)}
for (group_min, group_max), group in AGE_GROUP_MAP.items():
    for age, existing_value in age_group_map.items():
        # Skip if some age already has a group assignment
        if existing_value:
            continue
        if group_min <= age <= group_max:
            age_group_map[age] = str(group)

# Fill missing group assignments with regular age values
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
            "QUALITY_CLASS": pl.String
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
        SORTING_KEY=(
            col("AGE_GROUP")
            .str.split("...").list.get(0)
            .cast(pl.Int16)
        )
    )
    .sort(col("SORTING_KEY"))
    .drop(col("SORTING_KEY"))
)


###############
# Get colours #
###############

# Offset starting colours towards darker for better contrast on plot
offset_to_darker = len(set(age_group_map.values())) // 4
# Create a divide between non mature age groups and mature age group colour
max_age_offset = len(set(age_group_map.values())) // 3
colours = plot.get_colours(
    n=len(set(age_group_map.values())) + offset_to_darker + max_age_offset,
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


layout = plotly.graph_objects.Layout(
    barmode="relative",
    bargroupgap=0.1,
    bargap=0.1,
    height=1440,
    width=1000,
    plot_bgcolor="white",
    title={
        "text": PLOT_TITLE,
        "font": {"size": 50},
        "x": 0.5,
        "y": 0.94
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
        },
        {
            "text": f'{PLOT_SUBTITLE} ({YEAR})',
            "xref": "paper",
            "yref": "paper",
            "xanchor": "center",
            "yanchor": "bottom",
            "x": 0.47,
            "y": 1.07,
            "showarrow": False,
            "font": {"size": 30},
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

plotly.io.write_image(
    figure,
    SAVE_PATH,
    format="png"
)
