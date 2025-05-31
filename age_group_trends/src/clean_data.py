# standard
import os
# external
import polars as pl
from polars import col


#########
# Input #
#########

root_dir = "age_group_trends"
age_group_raw_path = "data/raw/1.11.X Vanuseklassid + uuend_data.csv"
cutting_raw_path = "data/raw/3.2.2.X Raiete ajalugu_data.csv"
age_group_save_path = "data/clean/age_group.csv"
regeneration_cutting_save_path = "data/clean/regeneration_cutting.csv"

translations = {
    "Selguseta ala": "unknown",
    "Lage ala": "clearcut"
}


#############
# Read data #
#############

age_group_raw = pl.read_csv(os.path.join(root_dir, age_group_raw_path), encoding="utf-8", separator=";")
cutting_raw = pl.read_csv(os.path.join(root_dir, cutting_raw_path), encoding="utf-8", separator=";")

age_group = (
    age_group_raw
    .with_columns(
        AREA = (
            col("Meetriku väärtus")
            .str.replace(r"\s", "")
            .str.replace(",", ".")
            .cast(pl.Decimal(10, 2))
        ),
        UNIT = pl.when(col("Meetrik") == "Pindala (tuhat ha)").then(pl.lit("kha")),
        AGE_GROUP = (
            col("Kaitsepõhjus")
            .str.strip_chars()
            .replace(translations)
        )
    )
    .filter(
        col("AGE_GROUP") != pl.lit("Kokku")
    )
    .select(
        col("Aasta").alias("YEAR"),
        col("AGE_GROUP"),
        col("AREA"),
        col("UNIT")
    )
    .sort(col("YEAR"))
)

regeneration_cutting = (
    cutting_raw
    .with_columns(
        AREA = (
            col("Meetriku väärtus")
            .str.replace(r"\s", "")
            .str.replace(",", ".")
            .cast(pl.Decimal(10, 2))
        ),
        UNIT = pl.when(col("Meetrik") == "Pindala (tuhat ha)").then(pl.lit("kha"))
    )
    .filter(
        col("UNIT") == pl.lit("kha"),
        col("Kaitsepõhjus") == pl.lit("Uuendusraie kokku")
    )
    .select(
        col("Raie aasta").alias("YEAR"),
        col("AREA"),
        col("UNIT")
    )
    .sort(col("YEAR"))
)


#############
# Save data #
#############

age_group.write_csv(
    os.path.join(root_dir, age_group_save_path),
    separator=","
)

regeneration_cutting.write_csv(
    os.path.join(root_dir, regeneration_cutting_save_path),
    separator=","
)
