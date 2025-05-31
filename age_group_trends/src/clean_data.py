# standard
import os
# external
import polars as pl
from polars import col


#########
# Input #
#########

root_dir = "age_group_trends"
age_group_all_raw_path = "data/raw/1.11.X Vanuseklassid + uuend_kõik.csv"
age_group_production_raw_path = "data/raw/1.11.X Vanuseklassid + uuend_majandatav.csv"
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

age_group_all_raw = pl.read_csv(os.path.join(root_dir, age_group_all_raw_path), encoding="utf-8", separator=";")
age_group_production_raw = pl.read_csv(os.path.join(root_dir, age_group_production_raw_path), encoding="utf-8", separator=";")
cutting_raw = pl.read_csv(os.path.join(root_dir, cutting_raw_path), encoding="utf-8", separator=";")

age_group_all = (
    age_group_all_raw
    .with_columns(
        AREA = (
            col("Meetriku väärtus")
            .str.replace(r"\s", "")
            .str.replace(",", ".")
            .fill_null(0)
            .cast(pl.Decimal(10, 2))
        ),
        UNIT = pl.when(col("Meetrik") == "Pindala (tuhat ha)").then(pl.lit("kha")),
        AGE_GROUP = (
            col("Kaitsepõhjus")
            .str.strip_chars()
            .replace(translations)
        ),
        TYPE = pl.lit("all")
    )
    .filter(
        col("AGE_GROUP") != pl.lit("Kokku")
    )
    .select(
        col("Aasta").alias("YEAR"),
        col("TYPE"),
        col("AGE_GROUP"),
        col("AREA"),
        col("UNIT")
    )
)

age_group_production = (
    age_group_production_raw
    .with_columns(
        AREA = (
            col("Meetriku väärtus")
            .str.replace(r"\s", "")
            .str.replace(",", ".")
            .fill_null(0)
            .cast(pl.Decimal(10, 2))
        ),
        UNIT = pl.when(col("Meetrik") == "Pindala (tuhat ha)").then(pl.lit("kha")),
        AGE_GROUP = (
            col("Kaitsepõhjus")
            .str.strip_chars()
            .replace(translations)
        ),
        TYPE = pl.lit("production")
    )
    .filter(
        col("AGE_GROUP") != pl.lit("Kokku")
    )
    .select(
        col("Aasta").alias("YEAR"),
        col("TYPE"),
        col("AGE_GROUP"),
        col("AREA"),
        col("UNIT")
    )
)

age_group = (
    age_group_all
    .rename({"AREA": "AREA_ALL"})
    .drop("TYPE")
    .join(
        age_group_production.rename({"AREA": "AREA_PRODUCTION"}).drop("TYPE"),
        on=["YEAR", "AGE_GROUP", "UNIT"],
        how="left"
    )
    .with_columns(
        AREA_PROTECTED = col("AREA_ALL") - col("AREA_PRODUCTION")
    )
    .unpivot(
        index=["YEAR", "AGE_GROUP", "UNIT"],
        on=["AREA_PRODUCTION", "AREA_PROTECTED"],
        value_name="AREA",
        variable_name="TYPE"
    )
    .with_columns(
        TYPE=(
            col("TYPE")
            .str.replace("AREA_", "")
            .str.to_lowercase()
        )
    )
    .select(
        col("YEAR"),
        col("AGE_GROUP"),
        col("TYPE"),
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
