# standard
import os
from pathlib import Path
# external
import polars as pl
from polars import col


################
# Translations #
################

TRANSLATION_MAP = {
    "Selguseta ala": "renewal_not_complete",
    "Lage ala": "no_trees",
    "Kokku": "all",
    "Haab": "aspen",
    "Kask": "birch",
    "Sanglepp": "black_alder",
    "Hall lepp": "grey_alder",
    "Teised": "other",
    "Mänd": "pine",
    "Kuusk": "spruce",
    "all": "kokku",
    "aspen": "haab",
    "birch": "kask",
    "black_alder": "sanglepp",
    "grey_alder": "hall_lepp",
    "other": "teised",
    "pine": "mänd",
    "spruce": "kuusk",
    "RMK": "state_forest_management_centre",
    "Majandatav metsamaa": "production_forest",
    "Mittemajandatavad metsad": "protected_forest",
    "Kogu metsamaa": "all"
}


################
# Manual input #
################

ROOT_DIR_PATH = "age_pyramid"

# get raw data from Estonian National Forest Inventory tableau data
# https://tableau.envir.ee/views/SMI/17Vanuseklassidaegrida?%3Aembed=y > click on table heading > "View data..." > "Download"
AGE_GROUP_RAW_PATHS = """
    data/raw/17 Vanuseklassid aegrida tabel_data_all_all.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_aspen_all.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_birch_all.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_black_alder_all.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_grey_alder_all.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_other_all.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_pine_all.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_spruce_all.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_all_production.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_aspen_production.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_birch_production.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_black_alder_production.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_grey_alder_production.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_other_production.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_pine_production.csv,
    data/raw/17 Vanuseklassid aegrida tabel_data_spruce_production.csv
"""

SAVE_PATH = "data/clean/area_by_age_group.csv"


#############
# Env input #
#############

# Manual inputs act as defaults and can be overridden by env inputs
ROOT_DIR_PATH = os.getenv("ROOT_DIR_PATH", ROOT_DIR_PATH)
AGE_GROUP_RAW_PATHS = os.getenv("AGE_GROUP_RAW_PATHS", AGE_GROUP_RAW_PATHS)
SAVE_PATH = os.getenv("SAVE_PATH", SAVE_PATH)


#############
# Load data #
#############

age_group_raw_paths = [file_name.strip(" \n") for file_name in AGE_GROUP_RAW_PATHS.split(",")]

data_raw = pl.DataFrame()
for relative_path in age_group_raw_paths:
    file_path = Path(ROOT_DIR_PATH) / relative_path
    with open(file_path, encoding="utf-8") as read_file:
        data_current_file = pl.read_csv(
            read_file,
            separator=";"
        )
    # Add to existing
    data_raw = pl.concat([
        data_raw,
        data_current_file
    ])


##############
# Clean data #
##############

all_and_production_data = (
    data_raw
    .with_columns(
        AREA=(
            col("Meetriku väärtus")
            .str.replace(r"\s", "")
            .str.replace(",", ".")
            .fill_null(0)
            .cast(pl.Float64)
        ),
        UNIT=(
            pl.when(col("Meetrik") == "Pindala (tuhat ha)")
            .then(pl.lit("kha"))
        ),
        DOMINANT_SPECIES=(
            col("Enamuspuuliik")
            .str.strip_chars()
            .replace(TRANSLATION_MAP)
        ),
        AGE_GROUP=(
            col("Kaitsepõhjus")
            .str.strip_chars()
            .replace(TRANSLATION_MAP)
        ),
        ECONOMIC_CATEGORY=(
            col("Majanduskategooria")
            .str.strip_chars()
            .replace(TRANSLATION_MAP)
        )
    )
    .select(
        col("Aasta").alias("YEAR"),
        col("ECONOMIC_CATEGORY"),
        col("DOMINANT_SPECIES"),
        col("AGE_GROUP"),
        col("AREA"),
        col("UNIT")
    )
)

# Calculate protected areas by subtracting production areas from all areas
all_data = (
    all_and_production_data
    .filter(
        col("ECONOMIC_CATEGORY") == TRANSLATION_MAP["Kogu metsamaa"]
    )
)
production_data = (
    all_and_production_data
    .filter(
        col("ECONOMIC_CATEGORY") == TRANSLATION_MAP["Majandatav metsamaa"]
    )
)

age_group_data = (
    all_data
    .join(
        production_data,
        on=["YEAR", "DOMINANT_SPECIES", "AGE_GROUP", "UNIT"],
        how="left",
        suffix="_PRODUCTION"
    )
    .with_columns(
        AREA_PROTECTED = col("AREA") - col("AREA_PRODUCTION")
    )
    .unpivot(
        index=["YEAR", "DOMINANT_SPECIES", "AGE_GROUP", "UNIT"],
        on=["AREA_PRODUCTION", "AREA_PROTECTED"],
        value_name="AREA",
        variable_name="ECONOMIC_CATEGORY"
    )
    .with_columns(
        ECONOMIC_CATEGORY=pl.when(
            col("ECONOMIC_CATEGORY") == "AREA_PRODUCTION"
        ).then(
            pl.lit(TRANSLATION_MAP["Majandatav metsamaa"])
        ).when(
            col("ECONOMIC_CATEGORY") == "AREA_PROTECTED"
        ).then(
            pl.lit(TRANSLATION_MAP["Mittemajandatavad metsad"])
        )
    )
    .select(
        col("YEAR"),
        col("DOMINANT_SPECIES"),
        col("AGE_GROUP"),
        col("ECONOMIC_CATEGORY"),
        col("AREA"),
        col("UNIT")
    )
)


############
# Validate #
############

tolerated_deviation_kha = 0.3     # 300 ha

# Validate that total and individual species/age group areas match in raw data
raw_area_by_species_and_age_group = (
    all_and_production_data
    .filter(
        (col("ECONOMIC_CATEGORY") == TRANSLATION_MAP["Kogu metsamaa"]) &
        (col("DOMINANT_SPECIES") != TRANSLATION_MAP["Kokku"]) &
        (col("AGE_GROUP") != TRANSLATION_MAP["Kokku"])
    )
    .select(col("AREA"))
    .to_series()
    .sum()
)

raw_area_by_species_and_age_group_totals = (
    all_and_production_data
    .filter(
        (col("ECONOMIC_CATEGORY") == TRANSLATION_MAP["Kogu metsamaa"]) &
        (col("DOMINANT_SPECIES") == TRANSLATION_MAP["Kokku"]) &
        (col("AGE_GROUP") == TRANSLATION_MAP["Kokku"])
    )
    .select(col("AREA"))
    .to_series()
    .sum()
)

if abs(raw_area_by_species_and_age_group - raw_area_by_species_and_age_group_totals) > tolerated_deviation_kha:
    raise ValueError(f'Total area by individual species/age group ({raw_area_by_species_and_age_group} kha) does not match the total area by the "all" species/age group rows ({raw_area_by_species_and_age_group_totals} kha)')

# Validate that total clean area matches total raw area
clean_area = (
    age_group_data
    .filter(
        col("DOMINANT_SPECIES") != TRANSLATION_MAP["Kokku"],
        col("AGE_GROUP") != TRANSLATION_MAP["Kokku"]
    )
    .select(col("AREA"))
    .to_series()
    .sum()
)

if abs(clean_area - raw_area_by_species_and_age_group) > tolerated_deviation_kha:
    raise ValueError(f'Total area after cleaning by individual species/age group ({clean_area} kha) does not match the total area by the "all" species/age group rows from raw data ({raw_area_by_species_and_age_group} kha)')


#######################
# Remove summary rows #
#######################

save_data = (
    age_group_data
    # Remove summary rows
    .filter(
        col("DOMINANT_SPECIES") != TRANSLATION_MAP["Kokku"],
        col("AGE_GROUP") != TRANSLATION_MAP["Kokku"]
    )
    # Round area to 2 decimal places to avoid float artefacts
    .with_columns(
        AREA=col("AREA").round(2)
    )
    .sort(
        col("YEAR"),
        col("DOMINANT_SPECIES"),
        col("ECONOMIC_CATEGORY"),
        col("AGE_GROUP")
    )
)


########
# Save #
########

save_path = Path(ROOT_DIR_PATH) / SAVE_PATH
save_path.parent.mkdir(parents=True, exist_ok=True)

with open(save_path, "w", encoding="utf-8") as save_file:
    save_data.write_csv(
        save_file,
        separator=","
    )
