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

age_group_aggregated = {
    "clearcut":     "0...20",
    "...10":        "0...20",
    "11...20":      "0...20",
    "21...30":      "21...40",
    "31...40":      "21...40",
    "41...50":      "41...60",
    "51...60":      "41...60",
    "61...70":      "61...",
    "71...80":      "61...",
    "81...90":      "61...",
    "91...100":     "61...",
    "101...110":    "61...",
    "111...120":    "61...",
    "121...130":    "61...",
    "131...140":    "61...",
    "141...":       "61..."
}


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

regeneration_cutting_prepared = (
    regeneration_cutting
    .with_columns(
        TYPE=pl.lit("production"),
        CATEGORY=pl.lit("regeneration cutting")
    )
    .select(
        col("YEAR"),
        col("TYPE"),
        col("CATEGORY"),
        col("AREA"),
        col("UNIT")
    )
)

regeneration_cutting_protected = (
    regeneration_cutting
    .with_columns(
        TYPE=pl.lit("protected"),
        CATEGORY=pl.lit("regeneration cutting"),
        AREA=pl.lit(0.0)
    )
    .select(
        col("YEAR"),
        col("TYPE"),
        col("CATEGORY"),
        col("AREA"),
        col("UNIT")
    )
)

regeneration_cutting_prepared = (
    pl.concat([
        regeneration_cutting_prepared,
        regeneration_cutting_protected
    ])
)


age_group_unknown = (
    age_group
    .filter(col("AGE_GROUP") == "unknown")
)

age_group_totals = (
    age_group
    .filter(col("AGE_GROUP") != "unknown")
    .group_by([
        col("YEAR"),
        col("TYPE")
    ])
    .agg(
        pl.col("AREA").sum().alias("AREA"),
    )
)

age_group_prepared = (
    age_group
    # Add unknown area to the age group area proportionately
    .filter(col("AGE_GROUP") != "unknown")
    .join(
        age_group_totals,
        on=["YEAR", "TYPE"],
        how="left",
        suffix="_TOTAL"
    )
    .join(
        age_group_unknown,
        on=["YEAR", "TYPE"],
        how="left",
        suffix="_UNKNOWN"
    )
    .with_columns(
        AREA=col("AREA") + (col("AREA") / col("AREA_TOTAL") * col("AREA_UNKNOWN"))
    )
    # Aggregate age groups into broader categories
    .with_columns(
        CATEGORY=col("AGE_GROUP").replace(age_group_aggregated)
    )
    .group_by([
        col("YEAR"),
        col("TYPE"),
        col("CATEGORY")
    ])
    .agg(
        col("AREA").sum().alias("AREA"),
        col("UNIT").first().alias("UNIT")
    )
    .select(
        col("YEAR"),
        col("TYPE"),
        col("CATEGORY"),
        col("AREA"),
        col("UNIT")
    )
)

# Add regeneration cutting areas
# Subtract regeneration cutting areas from highest age group production area
prepared_data = (
    pl.concat([
        age_group_prepared,
        regeneration_cutting_prepared
    ])
    .join(
        regeneration_cutting_prepared,
        on=["YEAR", "TYPE"],
        how="left",
        suffix="_REGENERATION_CUTTING"
    )
    .with_columns(
        AREA_REGENERATION_CUTTING=col("AREA_REGENERATION_CUTTING").fill_null(0)
    )
    .with_columns(
        AREA=pl.when(
            (col("TYPE") == "production") & (col("CATEGORY") == list(age_group_aggregated.values())[-1]))
            .then(col("AREA") - col("AREA_REGENERATION_CUTTING"))
            .otherwise(col("AREA"))
            .round(2)
    )
    .select(
        col("YEAR"),
        col("TYPE"),
        col("CATEGORY"),
        col("AREA"),
        col("UNIT")
    )
)

production_areas = (
    prepared_data
    .filter(col("TYPE") == "production")
    .pivot(
        index=["YEAR", "UNIT", "TYPE"],
        on="CATEGORY",
        values="AREA",
        sort_columns=True
    )
    .with_columns(pl.exclude("YEAR").fill_null(0))
    .sort(col("YEAR"))
)

protected_areas = (
    prepared_data
    .filter(col("TYPE") == "protected")
    .pivot(
        index=["YEAR", "UNIT", "TYPE"],
        on="CATEGORY",
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
