# standard
import os
from pathlib import Path
from typing import Optional
# external
import polars as pl
from polars import col
import tqdm


################
# Manual input #
################

ROOT_DIR_PATH = "age_pyramid"

AREA_BY_QUALITY_CLASS_DATA_PATH = "data/clean/area_by_quality_class.csv"
AREA_BY_AGE_GROUP_DATA_PATH = "data/clean/area_by_age_group.csv"
MATURITY_AGE_DATA_PATH = "data/clean/maturity_age.csv"

SAVE_PATH = "data/clean/optimal_age_pyramid_areas.csv"

# Proportion of the remaining mature forest cut every year
STANDARD_ANNUAL_MATURE_CUT_PROPORTION: float = 0.055
# Proportion of non-renewed (production) area
STANDARD_NON_RENEWED_PROPORTION: float = 0.1
# Ensures that the saved areas include at least a minimum number of age groups
MINIMUM_TOP_AGE: int = 131

# Default maturity ages to use when no legal maturity age is set
ASPEN_DEFAULT_MATURITY_AGE = 30
BLACK_ALDER_DEFAULT_MATURITY_AGE = 30
GREY_ALDER_DEFAULT_MATURITY_AGE = 30


#############
# Env input #
#############

# Manual inputs act as defaults and can be overridden by env inputs
ROOT_DIR_PATH = os.getenv("ROOT_DIR_PATH", ROOT_DIR_PATH)
AREA_BY_QUALITY_CLASS_DATA_PATH = os.getenv("AREA_BY_QUALITY_CLASS_DATA_PATH", AREA_BY_QUALITY_CLASS_DATA_PATH)
AREA_BY_AGE_GROUP_DATA_PATH = os.getenv("AREA_BY_AGE_GROUP_DATA_PATH", AREA_BY_AGE_GROUP_DATA_PATH)
MATURITY_AGE_DATA_PATH = os.getenv("MATURITY_AGE_DATA_PATH", MATURITY_AGE_DATA_PATH)
SAVE_PATH = os.getenv("SAVE_PATH", SAVE_PATH)

STANDARD_ANNUAL_MATURE_CUT_PROPORTION = float(os.getenv("STANDARD_ANNUAL_MATURE_CUT_PROPORTION", STANDARD_ANNUAL_MATURE_CUT_PROPORTION))
STANDARD_NON_RENEWED_PROPORTION = float(os.getenv("STANDARD_NON_RENEWED_PROPORTION", STANDARD_NON_RENEWED_PROPORTION))
MINIMUM_TOP_AGE = int(os.getenv("MINIMUM_TOP_AGE", MINIMUM_TOP_AGE))

ASPEN_DEFAULT_MATURITY_AGE = int(os.getenv("ASPEN_DEFAULT_MATURITY_AGE", ASPEN_DEFAULT_MATURITY_AGE))
BLACK_ALDER_DEFAULT_MATURITY_AGE = int(os.getenv("BLACK_ALDER_DEFAULT_MATURITY_AGE", BLACK_ALDER_DEFAULT_MATURITY_AGE))
GREY_ALDER_DEFAULT_MATURITY_AGE = int(os.getenv("GREY_ALDER_DEFAULT_MATURITY_AGE", GREY_ALDER_DEFAULT_MATURITY_AGE))


#########################
# Functions and classes #
#########################

def get_optimal_pyramid_areas(
    total_area: float,
    maturity_age: int,
    annual_mature_cut_proportion: float,
    non_renewed_proportion: float,
    minimum_top_age: Optional[int] = None
) -> list[dict]:
    """
    Calculate the optimal area distribution across age groups by total area and maturity age.
    Use the following model:
    - total_area = non_renewed_area + renewed_non_mature_area + mature_area
    - non_renewed_area = non_renewed_proportion * total_area
    - renewed_non_mature_area = (maturity_age - 1) * optimal_area_per_age_group
    - mature_area = optimal_area_per_age_group * (1 - annual_mature_cut proportion) / annual_mature_cut_proportion

    The mature area formula is the sum of a geometric series where each year a proportion of the remaining mature area is cut.

    The optional top_age_group parameter ensures that the returned areas include at least a minimum number of age groups.
    This is useful for generating age pyramid plots for comparison. Each plot will have at least some minimum number of age groups.

    Returns a list of dicts where each dict represents a single age with corresponding area and maturity class.
    """
    if not minimum_top_age:
        # Don't set a minimum top age group
        minimum_top_age = 0

    if maturity_age == 0:
        # Age 0 means the forest that is not renewed yet. Some proportion can be cut only from forest that is at least 1 year old.
        maturity_age = 1

    optimal_area_per_age_group = (total_area - non_renewed_proportion * total_area) / (maturity_age - 1 + (1 - annual_mature_cut_proportion) / (annual_mature_cut_proportion))

    # Get areas where the forest is not renewed yet: clear cut + very young trees
    non_renewed_areas = [{
        "AGE": 0,
        "AREA": non_renewed_proportion * total_area,
        "MATURITY_CLASS": "non_renewed"
    }]

    # Get renewed non-mature areas: classified as forest, but age of trees below maturity age
    renewed_non_mature_areas = []
    for age_group in range(1, maturity_age):
        renewed_non_mature_areas += [{
            "AGE": age_group,
            "AREA": optimal_area_per_age_group,
            "MATURITY_CLASS": "renewed_non_mature"
        }]

    # Get mature areas: age of trees above maturity age
    remaining_mature_area = optimal_area_per_age_group * (1 - annual_mature_cut_proportion) / annual_mature_cut_proportion
    mature_areas = []
    age = maturity_age
    while (remaining_mature_area > (total_area * 1e-4)) or (age <= minimum_top_age):
        area = optimal_area_per_age_group * (1 - annual_mature_cut_proportion)**(age - maturity_age + 1)
        mature_areas += [{
            "AGE": age,
            "AREA": area,
            "MATURITY_CLASS": "mature"
        }]
        remaining_mature_area -= area
        age += 1

    # Combine all areas
    areas = non_renewed_areas + renewed_non_mature_areas + mature_areas
    return areas


#############
# Load data #
#############

area_by_quality_class_data_path = Path(ROOT_DIR_PATH) / AREA_BY_QUALITY_CLASS_DATA_PATH
with open(area_by_quality_class_data_path, encoding="utf-8") as read_file:
    area_by_quality_class_data = pl.read_csv(read_file)

area_by_age_group_data_path = Path(ROOT_DIR_PATH) / AREA_BY_AGE_GROUP_DATA_PATH
with open(area_by_age_group_data_path, encoding="utf-8") as read_file:
    area_by_age_group_data = pl.read_csv(read_file)

maturity_age_data_path = Path(ROOT_DIR_PATH) / MATURITY_AGE_DATA_PATH
with open(maturity_age_data_path, encoding="utf-8") as read_file:
    maturity_age_data = pl.read_csv(read_file)


######################################
# Process area by quality class data #
######################################

area_by_quality_class_processed = (
    area_by_quality_class_data
    .with_columns(
        # Assume missing area means 0 area
        AREA_RENEWED=col("AREA").fill_null(0.0)
    )
)


##################################
# Process non renewed areas data #
##################################

non_renewed_areas_data = (
    area_by_age_group_data
    .filter(
        col("AGE_GROUP").is_in(["no_trees", "renewal_not_complete"])
    )
    .group_by(
        col("YEAR"),
        col("DOMINANT_SPECIES"),
        col("ECONOMIC_CATEGORY")
    )
    .agg(
        # Aggregate AGE_GROUP
        AREA_NON_RENEWED_ALL=col("AREA").sum()
    )
)

# Assume non-renewed area is distributed proportionally across quality classes and management types
non_renewed_areas_processed = (
    area_by_quality_class_processed
    .join(
        non_renewed_areas_data,
        how="left",
        left_on=[
            col("YEAR"),
            col("DOMINANT_SPECIES"),
            col("ECONOMIC_CATEGORY")
        ],
        right_on=[
            col("YEAR"),
            col("DOMINANT_SPECIES"),
            col("ECONOMIC_CATEGORY")
        ]
    )
    .with_columns(
        # Proportion of area over aggregated QUALITY_CLASS and MANAGED_BY
        AREA_PROPORTION=(
            col("AREA_RENEWED") / col("AREA_RENEWED").sum().over([
                col("YEAR"),
                col("ECONOMIC_CATEGORY"),
                col("DOMINANT_SPECIES")
            ])
        )
    )
    .with_columns(
        AREA_NON_RENEWED=col("AREA_PROPORTION") * col("AREA_NON_RENEWED_ALL")
    )
    .select(
        col("YEAR"),
        col("MANAGED_BY"),
        col("ECONOMIC_CATEGORY"),
        col("DOMINANT_SPECIES"),
        col("QUALITY_CLASS"),
        col("AREA_NON_RENEWED")
    )
    .sort(
        col("YEAR"), col("DOMINANT_SPECIES"), col("ECONOMIC_CATEGORY")
    )
)


#############################
# Process maturity age data #
#############################

# Make sure that all year/species/quality class combinations exist in the data
existing_species_quality_class_combinations = (
    area_by_quality_class_data
    .filter(
        col("ECONOMIC_CATEGORY") == "production_forest",
        col("QUALITY_CLASS") != "all",
    )
    .group_by(
        col("YEAR"),
        col("DOMINANT_SPECIES"),
        col("QUALITY_CLASS")
    )
    .agg()
)

maturity_age_other = (
    maturity_age_data
    .filter(
        col("SPECIES") == "hardwood"
    )
    .with_columns(
        SPECIES=pl.lit("other")
    )
)

maturity_age_5A_5B = (
    pl.concat([
        maturity_age_data,
        maturity_age_other
    ])
    .filter(
        col("QUALITY_CLASS") == "5A"
    )
    .with_columns(
        QUALITY_CLASS=pl.lit("5A-5B")
    )
)

years_with_maturity_age_data_aspen = (
    maturity_age_data
    .filter(
        col("SPECIES") == "aspen"
    
    )["YEAR"].unique().to_list()
)

years_with_maturity_age_data_black_alder = (
    maturity_age_data
    .filter(
        col("SPECIES") == "black_alder"
    
    )["YEAR"].unique().to_list()
)

maturity_age_processed = (
    existing_species_quality_class_combinations
    .join(
        pl.concat([
            maturity_age_data,
            # Assume that anything designated as "other" species has the same maturity age as hardwood
            maturity_age_other,
            # Assume that quality class 5A-5B has the same maturity age as 5A
            maturity_age_5A_5B
        ]),
        how="left",
        left_on=[col("YEAR"), col("DOMINANT_SPECIES"), col("QUALITY_CLASS")],
        right_on=[col("YEAR"), col("SPECIES"), col("QUALITY_CLASS")]
    )
    .with_columns(
        MATURITY_AGE=pl.when(
            # Assign maturity age 50 to aspen with quality class "5" and "5A-5B" for years with existing data
            (col("YEAR").is_in(years_with_maturity_age_data_aspen)) &
            (col("DOMINANT_SPECIES") == "aspen") &
            (col("QUALITY_CLASS").is_in(["5", "5A-5B"]))
        ).then(50)
        .when(
            # Assign maturity age 20 to aspen for years with no existing data
            ~(col("YEAR").is_in(years_with_maturity_age_data_aspen)) &
            (col("DOMINANT_SPECIES") == "aspen")
        )
        .then(ASPEN_DEFAULT_MATURITY_AGE)
        .when(
            # Assign maturity age 20 to black alder for years with no existing data
            ~(col("YEAR").is_in(years_with_maturity_age_data_black_alder)) &
            (col("DOMINANT_SPECIES") == "black_alder")
        )
        .then(BLACK_ALDER_DEFAULT_MATURITY_AGE)
        .when(
            # Assign maturity age 20 to grey alder (value not given in maturity age input data)
            col("DOMINANT_SPECIES") == "grey_alder"
        ).then(GREY_ALDER_DEFAULT_MATURITY_AGE)
        .otherwise(
            col("MATURITY_AGE")
        )
    )
)

######################
# Get pyramid inputs #
######################

pyramid_input_data = (
    area_by_quality_class_processed
    .join(
        maturity_age_processed,
        how="left",
        left_on=[col("YEAR"), col("DOMINANT_SPECIES"), col("QUALITY_CLASS")],
        right_on=[col("YEAR"), col("DOMINANT_SPECIES"), col("QUALITY_CLASS")]
    )
    .join(
        non_renewed_areas_processed,
        how="left",
        left_on=[col("YEAR"), col("DOMINANT_SPECIES"), col("QUALITY_CLASS"), col("MANAGED_BY"), col("ECONOMIC_CATEGORY")],
        right_on=[col("YEAR"), col("DOMINANT_SPECIES"), col("QUALITY_CLASS"), col("MANAGED_BY"), col("ECONOMIC_CATEGORY")]
    )
    .with_columns(
        AREA=col("AREA_RENEWED") + col("AREA_NON_RENEWED")
    )
    .filter(
        col("ECONOMIC_CATEGORY") == "production_forest"
    )
)

# Check for missing maturity ages
missing_maturity_ages = (
    pyramid_input_data
    .filter(
        col("MATURITY_AGE").is_null()
    )
)

if not missing_maturity_ages.is_empty():
    raise ValueError("Input information about some maturity ages is missing!")


####################
# Get pyramid data #
####################

pyramid_data = pl.DataFrame()
for input in tqdm.tqdm(pyramid_input_data.to_dicts(), desc="Calculating optimal age pyramid areas"):
    pyramid_rows = get_optimal_pyramid_areas(
        total_area=input["AREA"],
        maturity_age=input["MATURITY_AGE"],
        annual_mature_cut_proportion=STANDARD_ANNUAL_MATURE_CUT_PROPORTION,
        non_renewed_proportion=STANDARD_NON_RENEWED_PROPORTION,
        # Make sure there are at least as many age values as the input map has
        minimum_top_age=MINIMUM_TOP_AGE
    )
    pyramid_data_current_input = (
        pl.DataFrame(
            pyramid_rows,
            schema={
                "AGE": pl.Int16,
                "AREA": pl.Float32,
                "MATURITY_CLASS": pl.String,
            }
        )
        .with_columns(
            YEAR=pl.lit(input["YEAR"]),
            MANAGED_BY=pl.lit(input["MANAGED_BY"]),
            DOMINANT_SPECIES=pl.lit(input["DOMINANT_SPECIES"]),
            QUALITY_CLASS=pl.lit(input["QUALITY_CLASS"]),
            UNIT=pl.lit(input["UNIT"]),
            ANNUAL_MATURE_CUT_PROPORTION=pl.lit(STANDARD_ANNUAL_MATURE_CUT_PROPORTION),
            NON_RENEWED_PROPORTION=pl.lit(STANDARD_NON_RENEWED_PROPORTION)
        )
    )
    # Validate
    if abs(pyramid_data_current_input["AREA"].sum() - input["AREA"]) > (1e-3 * input["AREA"]):
        raise ValueError("Calculated pyramid areas do not sum up to the total area!")

    pyramid_data = pl.concat([
        pyramid_data,
        pyramid_data_current_input
    ])


########
# Save #
########

save_data = (
    pyramid_data
    .select(
        col("YEAR"),
        col("MANAGED_BY"),
        col("DOMINANT_SPECIES"),
        col("QUALITY_CLASS"),
        col("AGE"),
        col("AREA"),
        col("UNIT"),
        col("MATURITY_CLASS"),
        col("ANNUAL_MATURE_CUT_PROPORTION"),
        col("NON_RENEWED_PROPORTION")
    )
)

save_path = Path(ROOT_DIR_PATH) / SAVE_PATH
save_path.parent.mkdir(parents=True, exist_ok=True)

with open(save_path, "w", encoding="utf-8") as save_file:
    save_data.write_csv(
        save_file,
        separator=","
    )
