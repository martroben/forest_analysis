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
    "spruce": "kuusk"
}


#########
# Input #
#########

ROOT_DIR_PATH = "elf_smi"

# https://tableau.envir.ee/views/SMI/10Diameetrid?%3Aembed=y > click on table heading > "View data..." > "Download"
DIAMETER_RAW_PATHS = [
    "data/raw/10 Diameetri jaotus tabel_data_2011.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2012.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2013.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2014.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2015.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2016.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2017.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2018.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2019.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2020.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2021.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2022.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2023.csv",
    "data/raw/10 Diameetri jaotus tabel_data_2024.csv",
]

DIAMETER_SAVE_PATH = "data/clean/diameter.csv"


#############
# Load data #
#############

diameter_data_raw = pl.DataFrame()

for path in DIAMETER_RAW_PATHS:
    with open(os.path.join(ROOT_DIR_PATH, path), encoding="utf-8") as read_file:
        diameter_data_current_file = pl.read_csv(
            read_file,
            separator=";"
        )
    # Add to existing
    diameter_data_raw = pl.concat([
        diameter_data_raw,
        diameter_data_current_file
    ])


##############
# Clean data #
##############

diameter_data = (
    diameter_data_raw
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
            "Kaitsepõhjus",
            "Aasta",
            "Enamuspuuliik"
        ],
        values="Measure Values"
    )
    .with_columns(
        YEAR=col("Aasta"),
        DOMINANT_SPECIES = (
            col("Enamuspuuliik")
            .str.strip_chars()
            .replace(TRANSLATION_MAP)
        ),
        DIAMETER_CM_GROUP=(
            col("Kaitsepõhjus")
            .str.strip_chars()
            .replace(TRANSLATION_MAP)
            .replace("...2", "0...2")
        ),
        AREA=(
            col("Pindala (tuh ha)")
            .str.replace(",", ".")
            # .fill_null(0)
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
    .with_columns(
        # Temporary column for sorting values
        DIAMETER_SORTING_KEY=(
            col("DIAMETER_CM_GROUP")
            .str.split("...")
            .list.get(0)
            .replace("all", "999")
            .cast(pl.Int16)
        )
    )
    .sort(
        col("YEAR"),
        col("DOMINANT_SPECIES"),
        col("DIAMETER_SORTING_KEY")
    )
    .select(
        col("YEAR"),
        col("DOMINANT_SPECIES"),
        col("DIAMETER_CM_GROUP"),
        col("AREA"),
        col("UNIT"),
        col("RELATIVE_ERROR_PERCENT")
    )
)


############
# Validate #
############

areas_by_diameter_groups = (
    diameter_data
    .filter(col("DIAMETER_CM_GROUP") != "all")
    .select(col("AREA"))
    .fill_null(0)
    .to_series()
    .to_list()
)
areas_by_totals = (
    diameter_data
    .filter(col("DIAMETER_CM_GROUP") == "all")
    .select(col("AREA"))
    .fill_null(0)
    .to_series()
    .to_list()
)
if abs(sum(areas_by_diameter_groups) - sum(areas_by_totals)) > 1:
    raise ValueError(f'Total area by individual diameter groups species ({areas_by_diameter_groups} kha) does not match the total area by the diameter group "all" rows ({areas_by_totals}) kha')


########
# Save #
########

diameter_save_path = os.path.join(ROOT_DIR_PATH, DIAMETER_SAVE_PATH)
os.makedirs(
    os.path.dirname(diameter_save_path),
    exist_ok=True)

with open(diameter_save_path, "w", encoding="utf-8") as save_file:
    diameter_data.write_csv(
        save_file,
        separator=","
    )
