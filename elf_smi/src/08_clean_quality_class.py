# standard
import os
# external
import polars as pl
from polars import col


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
    "spruce": "kuusk",
    "RMK": "State Forest Management Centre",
    "Majandatav metsamaa": "production",
    "Mittemajandatavad metsad": "protected"
}


#########
# Input #
#########

ROOT_DIR_PATH = "elf_smi"

# https://tableau.envir.ee/views/SMI/10Diameetrid?%3Aembed=y > click on table heading > "View data..." > "Download"
QUALITY_CLASS_RAW_PATHS = [
    "data/raw/14 Boniteediklassid tabel_data_production_1999.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2000.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2001.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2002.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2003.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2004.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2005.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2006.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2007.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2008.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2009.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2010.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2011.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2012.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2013.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2014.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2015.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2016.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2017.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2018.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2019.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2020.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2021.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2022.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2023.csv",
    "data/raw/14 Boniteediklassid tabel_data_production_2024.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_1999.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2000.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2001.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2002.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2003.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2004.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2005.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2006.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2007.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2008.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2009.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2010.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2011.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2012.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2013.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2014.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2015.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2016.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2017.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2018.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2019.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2020.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2021.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2022.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2023.csv",
    "data/raw/14 Boniteediklassid tabel_data_protected_2024.csv"
]

QUALITY_CLASS_CLEAN_SAVE_PATH = "data/clean/quality_class.csv"

# TODO: not here, let's keep data as close to original as possible
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


#############
# Load data #
#############

quality_class_data_raw = pl.DataFrame()

for path in QUALITY_CLASS_RAW_PATHS:
    with open(os.path.join(ROOT_DIR_PATH, path), encoding="utf-8") as read_file:
        quality_class_data_current_file = pl.read_csv(
            read_file,
            separator=";"
        )
    # Add to existing
    quality_class_data_raw = pl.concat([
        quality_class_data_raw,
        quality_class_data_current_file
    ])


##############
# Clean data #
##############

quality_class_data = (
    quality_class_data_raw
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
        OWNER=(
            col("Omand")
            .str.strip_chars()
            .replace(TRANSLATION_MAP)
        ),
        TYPE=(
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
        col("DOMINANT_SPECIES") != "all"
    )
    .sort(
        col("YEAR"),
        col("OWNER"),
        col("TYPE"),
        col("DOMINANT_SPECIES"),
        col("QUALITY_CLASS")
    )
    .select(
        col("YEAR"),
        col("OWNER"),
        col("TYPE"),
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
    .filter(col("QUALITY_CLASS") != "all")
    .group_by(
        col("YEAR"),
        col("OWNER"),
        col("TYPE"),
        col("DOMINANT_SPECIES")
    )
    .agg(
        AREA_QUALITY_CLASS_SUM=col("AREA").sum()
    )
)
areas_all_quality_class = (
    quality_class_data
    .filter(col("QUALITY_CLASS") == "all")
    .group_by(
        col("YEAR"),
        col("OWNER"),
        col("TYPE"),
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
            col("OWNER"),
            col("TYPE"),
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
        col("OWNER"),
        col("TYPE"),
        col("DOMINANT_SPECIES")
    )
    .rows()
)
if non_matching_quality_class_totals:
    non_matching_quality_class_totals_strings = [f'{year} | {owner} | {type} | {species}' for year, owner, type, species in non_matching_quality_class_totals]
    error_message = f'The sum of areas by individual quality classes does not match the total area of the quality class "all" row for these categories:\n{"\n".join(non_matching_quality_class_totals_strings)}'
    raise ValueError(error_message)


########
# Save #
########

quality_class_save_path = os.path.join(ROOT_DIR_PATH, QUALITY_CLASS_CLEAN_SAVE_PATH)
os.makedirs(
    os.path.dirname(quality_class_save_path),
    exist_ok=True)

with open(quality_class_save_path, "w", encoding="utf-8") as save_file:
    quality_class_data.write_csv(
        save_file,
        separator=","
    )
