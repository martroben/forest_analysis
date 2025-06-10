# external
import polars as pl
from polars import col


def clean_age_group_data(data: pl.DataFrame, type_name: str, translations: dict) -> pl.DataFrame:
    """
    Discard age group totals (Kaitsepõhjus: Kokku).
    Convert Meetriku väärtus to float and rename to AREA.
    Set UNIT value to kha.
    Map translations to Kaitsepõhjus and rename to AGE_GROUP.
    Set TYPE to type_name.
    """
    out = (
        data
        .filter(
            col("Kaitsepõhjus").str.strip_chars() != pl.lit("Kokku")
        )
        .with_columns(
            AREA = (
                col("Meetriku väärtus")
                .str.replace(r"\s", "")
                .str.replace(",", ".")
                .fill_null(0)
                .cast(pl.Float64)
            ),
            UNIT = (
                pl.when(col("Meetrik") == "Pindala (tuhat ha)")
                .then(pl.lit("kha"))
            ),
            DOMINANT_SPECIES = (
                col("Enamuspuuliik")
                .str.strip_chars()
                .replace(translations)
            ),
            AGE_GROUP = (
                col("Kaitsepõhjus")
                .str.strip_chars()
                .replace(translations)
            ),
            TYPE = pl.lit(type_name)
        )
        .select(
            col("Aasta").alias("YEAR"),
            col("TYPE"),
            col("DOMINANT_SPECIES"),
            col("AGE_GROUP"),
            col("AREA"),
            col("UNIT")
        )
    )
    return out


def combine_all_and_production_data(all_data: pl.DataFrame, production_data: pl.DataFrame) -> pl.DataFrame:
    """
    Get protected areas by subtracting production areas from all economic areas.
    Round areas to 2 decimals.
    Return data frame with TYPE values "production" and "protected".
    """
    out = (
        all_data
        .rename({"AREA": "AREA_ALL"})
        .drop("TYPE")
        .join(
            production_data.rename({"AREA": "AREA_PRODUCTION"}).drop("TYPE"),
            on=["YEAR", "DOMINANT_SPECIES", "AGE_GROUP", "UNIT"],
            how="left"
        )
        .with_columns(
            AREA_PROTECTED = col("AREA_ALL") - col("AREA_PRODUCTION")
        )
        .unpivot(
            index=["YEAR", "DOMINANT_SPECIES", "AGE_GROUP", "UNIT"],
            on=["AREA_PRODUCTION", "AREA_PROTECTED"],
            value_name="AREA",
            variable_name="TYPE"
        )
        .with_columns(
            TYPE=(
                col("TYPE")
                .str.replace("AREA_", "")
                .str.to_lowercase()
            ),
            AREA=col("AREA").round(2)
        )
        .select(
            col("YEAR"),
            col("DOMINANT_SPECIES"),
            col("AGE_GROUP"),
            col("TYPE"),
            col("AREA"),
            col("UNIT")
        )
        .sort(col("YEAR"), col("DOMINANT_SPECIES"), col("TYPE"), col("AGE_GROUP"))
    )
    return out


def clean_regeneration_cutting_data(data: pl.DataFrame) -> pl.DataFrame:
    """
    Filter records of annual regeneration cutting total areas.
    Convert Meetriku väärtus to float and rename to AREA. Round to 2 decimals.
    Set UNIT value to kha.
    Rename Raie aasta to YEAR.
    """
    out = (
        data
        .filter(
            col("Meetrik") == pl.lit("Pindala (tuhat ha)"),
            col("Kaitsepõhjus") == pl.lit("Uuendusraie kokku")
        )
        .with_columns(
            AREA = (
                col("Meetriku väärtus")
                .str.replace(r"\s", "")
                .str.replace(",", ".")
                .cast(pl.Float64)
                .round(2)
            ),
            UNIT = pl.when(col("Meetrik") == "Pindala (tuhat ha)").then(pl.lit("kha"))
        )
        .select(
            col("Raie aasta").alias("YEAR"),
            col("AREA"),
            col("UNIT")
        )
        .sort(col("YEAR"))
    )
    return out
