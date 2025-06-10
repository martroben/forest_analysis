# external
import polars as pl
from polars import col


def align_regeneration_cutting_data(data: pl.DataFrame, year_min: int, year_max: int, type_name: str) -> pl.DataFrame:
    """
    Set regeneration cutting data to input year range.
    Set TYPE (production/protected) to input type_name.
    Fill missing AREA data with zeros.
    Fill missing UNIT data with kha.
    """
    year_type_data = pl.DataFrame({
        "YEAR": range(year_min, year_max + 1),
        "TYPE": [type_name] * (year_max - year_min + 1)
    })

    out = (
        year_type_data
        .join(
            data,
            on=col("YEAR"),
            how="left"
        )
        .with_columns(
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
    return out


def add_unknown_data(known: pl.DataFrame, unknown: pl.DataFrame) -> pl.DataFrame:
    """
    Add data with "unknown" age group proportionally to all known age groups.
    """
    out = (
        known
        .with_columns(
            AREA_YEAR_TYPE_TOTAL=pl.sum("AREA").over("YEAR", "TYPE")
        )
        .with_columns(
            AREA_PROPORTION=col("AREA") / col("AREA_YEAR_TYPE_TOTAL")
        )
        .join(
            unknown,
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
    return out


def aggregate_age_groups(data: pl.DataFrame, aggregation_map: dict) -> pl.DataFrame:
    """
    Aggregate age groups by input aggregation map.
    Set AREA to the sum of areas for each group.
    """
    out = (
        data
        .with_columns(
            AGE_GROUP=col("AGE_GROUP").replace(aggregation_map)
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
    return out


def subtract_regeneration_cutting(age_group: pl.DataFrame, regeneration_cutting: pl.DataFrame, threshold: int) -> pl.DataFrame:
    """
    Subtract regeneration cutting area proportionately from eligible age groups.
    Eligible age groups are the ones that have age equal or older to the input threshold age.
    """
    out = (
        age_group
        .with_columns(
            AGE_GROUP_START=col("AGE_GROUP").str.split("...").list.get(0).str.strip_chars().cast(pl.Int32)
        )
        .with_columns(
            IS_REGENERATION_CUTTING_ELIGIBLE=(col("AGE_GROUP_START") >= pl.lit(threshold))
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
            regeneration_cutting,
            on=["YEAR", "TYPE"],
            how="left",
            suffix="_REGENERATION_CUTTING"
        )
        .with_columns(
            # Subtract regeneration cutting area proportionately from eligible age groups
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
    return out


def get_areas(data: pl.DataFrame) -> pl.DataFrame:
    """
    Pivot each AGE_GROUP area into a separate field.
    Fill missing values with zero for all fields except YEAR.
    """
    out = (
        data
        .pivot(
            index=["YEAR", "UNIT", "TYPE"],
            on="AGE_GROUP",
            values="AREA",
            sort_columns=True
        )
        .with_columns(pl.exclude("YEAR").fill_null(0.0))
        .sort(col("YEAR"))
    )
    return out
