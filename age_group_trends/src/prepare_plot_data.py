# standard
import os
# external
import polars as pl
from polars import col


##########
# Inputs #
##########

root_dir = "age_group_trends"
age_group_path = "data/clean/age_group.csv"
regeneration_cutting_path = "data/clean/regeneration_cutting.csv"

production_areas_save_path = "data/plot/production_areas.csv"
protected_areas_save_path = "data/plot/protected_areas.csv"
production_regeneration_cutting_save_path = "data/plot/production_regeneration_cutting.csv"
protected_regeneration_cutting_save_path = "data/plot/protected_regeneration_cutting.csv"

age_group_aggregated = {
    "clearcut":     "0...20",
    "...10":        "0...20",
    "11...20":      "0...20",
    "21...30":      "21...40",
    "31...40":      "21...40",
    "41...50":      "41...60",
    "51...60":      "41...60",
    "61...70":      "61...80",
    "71...80":      "61...80",
    "81...90":      "81...",
    "91...100":     "81...",
    "101...110":    "81...",
    "111...120":    "81...",
    "121...130":    "81...",
    "131...140":    "81...",
    "141...":       "81..."
}

regeneration_cutting_age_threshold = 60


#############
# Read data #
#############

age_group = pl.read_csv(
    os.path.join(root_dir, age_group_path),
    encoding="utf-8",
    separator=",")

regeneration_cutting = pl.read_csv(
    os.path.join(root_dir, regeneration_cutting_path),
    encoding="utf-8",
    separator=",")


################
# Process data #
################

production_regeneration_cutting = (
    # Use the same year range as age_group
    age_group
    .select(col("YEAR"))
    .unique()
    .join(
        regeneration_cutting,
        on=col("YEAR"),
        how="left"
    )
    .with_columns(
        TYPE=pl.lit("production"),
        AREA=col("AREA").fill_null(0),
        UNIT=col("UNIT").fill_null("kha")
    )
    .select(
        col("YEAR"),
        col("TYPE"),
        col("AREA"),
        col("UNIT")
    )
    .sort(col("YEAR"))
)

protected_regeneration_cutting = (
    # Use the same year range as age_group
    age_group
    .select(col("YEAR"))
    .unique()
    .join(
        regeneration_cutting,
        on=col("YEAR"),
        how="left"
    )
    .with_columns(
        TYPE=pl.lit("protected"),
        # Assume negligible regeneration cutting in protected forests
        AREA=pl.lit(0.0),
        UNIT=col("UNIT").fill_null("kha")
    )
    .select(
        col("YEAR"),
        col("TYPE"),
        col("AREA"),
        col("UNIT")
    )
    .sort(col("YEAR"))
)

# Add unknown area to the age group area proportionately
age_group_unknown = (
    age_group
    .filter(col("AGE_GROUP") == "unknown")
)

age_group_unknown_added = (
    age_group
    .filter(col("AGE_GROUP") != "unknown")
    .with_columns(
        AREA_YEAR_TYPE_TOTAL=pl.sum("AREA").over("YEAR", "TYPE")
    )
    .with_columns(
        AREA_PROPORTION=col("AREA") / col("AREA_YEAR_TYPE_TOTAL")
    )
    .join(
        age_group_unknown,
        on=["YEAR", "TYPE"],
        how="left",
        suffix="_UNKNOWN"
    )
    .with_columns(
        AREA=col("AREA") + (col("AREA_PROPORTION") * col("AREA_UNKNOWN"))
    )
    .select(
        col("YEAR"),
        col("TYPE"),
        col("AGE_GROUP"),
        col("AREA"),
        col("UNIT")
    )
)

# Aggregate age groups into broader categories
age_group_aggregated = (
    age_group_unknown_added
    .with_columns(
        AGE_GROUP=col("AGE_GROUP").replace(age_group_aggregated)
    )
    .group_by([
        col("YEAR"),
        col("TYPE"),
        col("AGE_GROUP")
    ])
    .agg(
        col("AREA").sum().alias("AREA"),
        col("UNIT").first().alias("UNIT")
    )
)

# Subtract regeneration cutting areas from eligible areas
age_group_regeneration_subtracted = (
    age_group_aggregated
    .with_columns(
        AGE_GROUP_START=col("AGE_GROUP").str.split("...").list.get(0).str.strip_chars().cast(pl.Int32)
    )
    .with_columns(
        IS_REGENERATION_CUTTING_ELIGIBLE=(col("AGE_GROUP_START") > regeneration_cutting_age_threshold)
    )
    .with_columns(
        REGENERATION_CUTTING_AREA_PROPORTION=(
            pl.when(
                col("IS_REGENERATION_CUTTING_ELIGIBLE")
            )
            .then(col("AREA") / pl.sum("AREA").over("YEAR", "AGE_GROUP", "IS_REGENERATION_CUTTING_ELIGIBLE"))
            .otherwise(0)
        )
    )
    .join(
        pl.concat([
            production_regeneration_cutting,
            protected_regeneration_cutting
        ]),
        on=["YEAR", "TYPE"],
        how="left",
        suffix="_REGENERATION_CUTTING"
    )
    .with_columns(
        # Subtract regeneration cutting are proportionately from eligible age groups
        AREA=(
            col("AREA") - col("REGENERATION_CUTTING_AREA_PROPORTION") * col("AREA_REGENERATION_CUTTING")
        ).round(2)
    )
    .select(
        col("YEAR"),
        col("TYPE"),
        col("AGE_GROUP"),
        col("AREA"),
        col("UNIT")
    )
)

# Divide to production and protected areas
production_areas = (
    age_group_regeneration_subtracted
    .filter(col("TYPE") == "production")
    .pivot(
        index=["YEAR", "UNIT", "TYPE"],
        on="AGE_GROUP",
        values="AREA",
        sort_columns=True
    )
    .with_columns(pl.exclude("YEAR").fill_null(0))
    .sort(col("YEAR"))
)

protected_areas = (
    age_group_regeneration_subtracted
    .filter(col("TYPE") == "protected")
    .pivot(
        index=["YEAR", "UNIT", "TYPE"],
        on="AGE_GROUP",
        values="AREA",
        sort_columns=True
    )
    .with_columns(pl.exclude("YEAR").fill_null(0))
    .sort(col("YEAR"))
)


#############
# Save data #
#############

production_areas_save_path_full = os.path.join(root_dir, production_areas_save_path)
os.makedirs(
    os.path.dirname(production_areas_save_path_full),
    exist_ok=True)

production_areas.write_csv(
    production_areas_save_path_full,
    separator=","
)


protected_areas_save_path_full = os.path.join(root_dir, protected_areas_save_path)
os.makedirs(
    os.path.dirname(protected_areas_save_path_full),
    exist_ok=True)

protected_areas.write_csv(
    protected_areas_save_path_full,
    separator=","
)

production_regeneration_cutting_save_path_full = os.path.join(root_dir, production_regeneration_cutting_save_path)
os.makedirs(
    os.path.dirname(production_regeneration_cutting_save_path_full),
    exist_ok=True)

production_regeneration_cutting.write_csv(
    production_regeneration_cutting_save_path_full,
    separator=","
)

protected_regeneration_cutting_save_path_full = os.path.join(root_dir, protected_regeneration_cutting_save_path)
os.makedirs(
    os.path.dirname(protected_regeneration_cutting_save_path_full),
    exist_ok=True)

protected_regeneration_cutting.write_csv(
    protected_regeneration_cutting_save_path_full,
    separator=","
)
