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
# https://tableau.envir.ee/views/SMI/14Boniteediklassid?%3Aembed=y > click on table heading > "View data..." > "Download"
QUALITY_CLASS_RAW_PATHS = """
    data/raw/14 Boniteediklassid tabel_data_production_1999.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2000.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2001.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2002.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2003.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2004.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2005.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2006.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2007.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2008.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2009.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2010.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2011.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2012.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2013.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2014.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2015.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2016.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2017.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2018.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2019.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2020.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2021.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2022.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2023.csv,
    data/raw/14 Boniteediklassid tabel_data_production_2024.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_1999.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2000.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2001.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2002.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2003.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2004.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2005.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2006.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2007.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2008.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2009.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2010.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2011.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2012.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2013.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2014.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2015.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2016.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2017.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2018.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2019.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2020.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2021.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2022.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2023.csv,
    data/raw/14 Boniteediklassid tabel_data_protected_2024.csv
"""

SAVE_PATH = "data/clean/area_by_quality_class.csv"


#############
# Env input #
#############

# Manual inputs act as defaults and can be overridden by env inputs
ROOT_DIR_PATH = os.getenv("ROOT_DIR_PATH", ROOT_DIR_PATH)
QUALITY_CLASS_RAW_PATHS = os.getenv("AGE_GROUP_RAW_PATHS", QUALITY_CLASS_RAW_PATHS)
SAVE_PATH = os.getenv("SAVE_PATH", SAVE_PATH)


#############
# Load data #
#############

quality_class_raw_paths = [file_name.strip(" \n") for file_name in QUALITY_CLASS_RAW_PATHS.split(",")]

data_raw = pl.DataFrame()
for relative_path in quality_class_raw_paths:
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

quality_class_data = (
    data_raw
    .with_columns(
        MEASURE_NAME=(
            col("Measure Names")
            .str.strip_chars()
            .str.replace_all(r"\s+", " ")
        )
    )
    .pivot(
        on="MEASURE_NAME",
        index=[
            "Omand",
            "Boniteedi klass",
            "Majanduskategooria",
            "Aasta",
            "Enamuspuuliik"
        ],
        values="Measure Values"
    )
    .with_columns(
        YEAR=col("Aasta"),
        MANAGED_BY=(
            col("Omand")
            .str.strip_chars()
            .replace(TRANSLATION_MAP)
        ),
        ECONOMIC_CATEGORY=(
            col("Majanduskategooria")
            .str.strip_chars()
            .replace(TRANSLATION_MAP)
        ),
        DOMINANT_SPECIES=(
            col("Enamuspuuliik")
            .str.strip_chars()
            .replace(TRANSLATION_MAP)
        ),
        QUALITY_CLASS=(
            col("Boniteedi klass")
            .str.strip_chars()
            .replace(TRANSLATION_MAP)
        ),
        AREA=(
            col("Pindala (tuh ha)")
            .str.replace(",", ".")
            .cast(pl.Float64)
        ),
        UNIT=pl.lit("kha"),
        RELATIVE_ERROR_PERCENT=(
            col("Suht.viga (± %)")
            .str.replace(",", ".")
            .fill_null(0)
            .cast(pl.Float64)
        )
    )
    .filter(
        # There is no area data given for category "all" species and "all" quality class
        # Also no data for species "all" and type protected.
        col("DOMINANT_SPECIES") != TRANSLATION_MAP["Kokku"],
    )
    .sort(
        col("YEAR"),
        col("MANAGED_BY"),
        col("ECONOMIC_CATEGORY"),
        col("DOMINANT_SPECIES"),
        col("QUALITY_CLASS")
    )
    .select(
        col("YEAR"),
        col("MANAGED_BY"),
        col("ECONOMIC_CATEGORY"),
        col("DOMINANT_SPECIES"),
        col("QUALITY_CLASS"),
        col("AREA"),
        col("UNIT"),
        col("RELATIVE_ERROR_PERCENT")
    )
)


############
# Validate #
############

# Check if quality class "all" for a species / type equals the sum of different quality classes for the same species / type
areas_quality_class_sum = (
    quality_class_data
    .filter(col("QUALITY_CLASS") != TRANSLATION_MAP["Kokku"])
    .group_by(
        col("YEAR"),
        col("MANAGED_BY"),
        col("ECONOMIC_CATEGORY"),
        col("DOMINANT_SPECIES")
    )
    .agg(
        AREA_QUALITY_CLASS_SUM=col("AREA").sum()
    )
)
areas_all_quality_class = (
    quality_class_data
    .filter(col("QUALITY_CLASS") == TRANSLATION_MAP["Kokku"])
    .group_by(
        col("YEAR"),
        col("MANAGED_BY"),
        col("ECONOMIC_CATEGORY"),
        col("DOMINANT_SPECIES")
    )
    .agg(
        AREA_ALL_QUALITY_CLASS=col("AREA").sum()
    )
)
non_matching_quality_class_totals = (
    areas_quality_class_sum
    .join(
        areas_all_quality_class,
        on=[
            col("YEAR"),
            col("MANAGED_BY"),
            col("ECONOMIC_CATEGORY"),
            col("DOMINANT_SPECIES")
        ],
        how="left"
    )
    .with_columns(
        ERROR=(col("AREA_QUALITY_CLASS_SUM") - col("AREA_ALL_QUALITY_CLASS")).abs()
    )
    .filter(col("ERROR") > 1)
    .select(
        col("YEAR"),
        col("MANAGED_BY"),
        col("ECONOMIC_CATEGORY"),
        col("DOMINANT_SPECIES")
    )
    .rows()
)
if non_matching_quality_class_totals:
    non_matching_quality_class_totals_strings = [f'{year} | {ownership} | {type} | {species}' for year, ownership, type, species in non_matching_quality_class_totals]
    error_message = f'The sum of areas by individual quality classes does not match the total area of the quality class "all" row for these categories:\n{"\n".join(non_matching_quality_class_totals_strings)}'
    raise ValueError(error_message)


# Check if managed_by "all" equals the sum of "state_forest_management_centre" and "other"
areas_managed_by_sum = (
    quality_class_data
    .filter(col("MANAGED_BY") != TRANSLATION_MAP["Kokku"])
)["AREA"].sum()

areas_managed_by_all = (
    quality_class_data
    .filter(col("MANAGED_BY") == TRANSLATION_MAP["Kokku"])
)["AREA"].sum()

if abs(areas_managed_by_sum - areas_managed_by_all) > 1:
    raise ValueError('The sum of areas by individual ownership types does not match the total area of the ownership type "all" row!')


#######################
# Remove summary rows #
#######################

save_data = (
    quality_class_data
    .filter(
        # Remove summary rows, because these don't have a corresponding maturity age
        col("QUALITY_CLASS") != TRANSLATION_MAP["Kokku"],
        # Remove summary owner rows to avoid double counting
        col("MANAGED_BY") != TRANSLATION_MAP["Kokku"]
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
