# standard
import re
# external
import plotly
import polars as pl
from polars import col


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
            col("AGE_GROUP"),
            col("DOMINANT_SPECIES")
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
            IS_ELIGIBLE_REGENERATION_CUTTING=(col("AGE_GROUP_START") >= pl.lit(threshold))
        )
        .with_columns(
            AREA_PROPORTION_REGENERATION_CUTTING=(
                pl.when(
                    col("IS_ELIGIBLE_REGENERATION_CUTTING")
                )
                .then(col("AREA") / pl.sum("AREA").over("YEAR", "DOMINANT_SPECIES", "TYPE", "IS_ELIGIBLE_REGENERATION_CUTTING"))
                .otherwise(0)
            )
        )
        .join(
            regeneration_cutting,
            on=[
                col("YEAR"),
                col("TYPE"),
                col("DOMINANT_SPECIES")
            ],
            how="left",
            suffix="_REGENERATION_CUTTING"
        )
        .with_columns(
            col("AREA_REGENERATION_CUTTING").fill_null(0)
        )
        .with_columns(
            # Subtract regeneration cutting area proportionately from eligible age groups
            AREA_UNADJUSTED=col("AREA"),
            REGENERATION_CUTTING_ADJUSTMENT=-col("AREA_PROPORTION_REGENERATION_CUTTING") * col("AREA_REGENERATION_CUTTING")
        )
        .with_columns(
            AREA=(col("AREA") + col("REGENERATION_CUTTING_ADJUSTMENT")).round(2)
        )
    ).select(
        col("YEAR"),
        col("TYPE"),
        col("AGE_GROUP"),
        col("DOMINANT_SPECIES"),
        col("AREA_UNADJUSTED"),
        col("REGENERATION_CUTTING_ADJUSTMENT"),
        col("AREA"),
        col("UNIT")
    ).sort(
        col("YEAR"),
        col("TYPE"),
        col("DOMINANT_SPECIES"),
        col("AGE_GROUP")
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
            index=["YEAR", "UNIT", "TYPE", "DOMINANT_SPECIES"],
            on="AGE_GROUP",
            values="AREA",
            sort_columns=True
        )
        .with_columns(pl.exclude("YEAR").fill_null(0.0))
        .sort(col("YEAR"))
    )
    return out


def get_regeneration_cutting_plot_data(data: pl.DataFrame, unique_years: list[str], unique_types: list[str], unique_species: list[str]) -> pl.DataFrame:
    """
    Add all years, types and species to the regeneration cutting data, fill missing values with defaults and nulls.
    This allows using the same logic for generating traces as is used for areas.
    """
    types_in_data = (
        data
        .select(col("TYPE"))
        .to_series()
        .to_list()
    )
    for type in types_in_data:
        if type not in unique_types:
            raise ValueError(f'Type {type} in input regeneration cutting data is not present in unique types input: {unique_types}. Check that regeneration cutting data types have been aligned with areas data')

    all_values = (
        pl.DataFrame({"YEAR": unique_years})
        .join(
            pl.DataFrame({"TYPE": unique_types}),
            how="cross"
        )
        .join(
            pl.DataFrame({"DOMINANT_SPECIES": unique_species}),
            how="cross"
        )
    )
    out = (
        data
        .join(
            all_values,
            on=[
                col("YEAR"),
                col("TYPE"),
                col("DOMINANT_SPECIES")
            ],
            how="right"
        )
        .with_columns(
            AREA=col("AREA").fill_null(0.0),
            UNIT=col("UNIT").fill_null("kha")
        )
    )
    return out


def rgb_to_hex(rgb: str) -> str:
    """
    Convert string in the form of 'rgb(10, 20, 30)' to a hex string.
    """
    rgb_components = [int(x.strip()) for x in rgb.strip("rgb()").split(",")]
    hex = "#{0:02x}{1:02x}{2:02x}".format(*rgb_components)
    return hex


def get_colorscale_positions(n: int) -> list[float]:
    """
    Get n evenly spaced numbers between 1/n and 1.
    Used to get colorscale values.
    """
    return [i / n for i in range(1, n + 1)]


def get_colours(n: int, scale_name: str) -> list[str]:
    """
    Get n evenly spaced colours from a plotly colorscale.
    """
    scale_positions = get_colorscale_positions(n)

    colours_rgb = plotly.colors.sample_colorscale(
        scale_name,
        scale_positions
    )
    colours_hex = [rgb_to_hex(colour) for colour in colours_rgb]

    return colours_hex


def get_gridline_intervals(max_y_value: float) -> tuple[int, int]:
    """
    Return the intervals of y-axis major and minor gridlines.
    """
    if max_y_value >= 500:
        return (500, 100)
    if 500 > max_y_value >= 100:
        return (100, 100)
    if 100 > max_y_value >= 50:
        return (50, 10)
    return (10, 10)


def get_layout(title: str, x_axis_title: str, y_axis_title: str, legend_title: str, source: str, max_y_value: float) -> plotly.graph_objects.Layout:
    major_gridline_interval, minor_gridline_interval = get_gridline_intervals(max_y_value)

    layout = plotly.graph_objects.Layout(
        barmode="stack",
        bargroupgap=0.1,
        bargap=0.1,
        height=1300,
        width=3600,
        plot_bgcolor="white",
        title={
            "text": title,
            "font": {"size": 50},
            "x": 0.5,           
            "xanchor": "center" 
        },
        xaxis={
            "title": {
                "text": x_axis_title,
                "font": {"size": 28},
                "standoff": 60
            },
            "dtick": 1,                             # Show label for every year
            "tickfont": {"size": 24}
        },
        yaxis={
            "gridcolor": "gray",
            "tickfont": {"size": 24},
            "dtick": major_gridline_interval,       # Major gridlines
            "minor": {                              # Minor gridlines
                "dtick": minor_gridline_interval,  
                "gridcolor": "lightgray",
                "gridwidth": 0.5
            },
            "title": {
                "text": y_axis_title,
                "font": {"size": 28},
                "standoff": 45
            }
        },
        margin={
            "pad": 20,                              # Axis label padding
            "t": 250,
            "l": 200,
            "b": 200,
            "r": 400
        },
        legend={
            "font": {"size": 24},
            "title": {
                "text": legend_title,
                "font": {"size": 28}
            }
        },
        annotations=[
            {
                "text": source,
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": -0.2,
                "showarrow": False,
                "font": {"size": 20},
                "align": "left"
            }
        ]
    )
    return layout


def apply_colour_to_substring(string: str, substring_colour_map: dict[str, str]) -> str:
    """
    Apply HTML bold + colour formatting to a substring of the input string.
    """
    out = string
    for substring, colour in substring_colour_map.items():
        if not substring in out:
            continue
        if f'>{substring}<' in out:
            # Skip if formatting is already applied
            continue
        out = re.sub(
            fr'\b{substring}\b',
            fr"<b><span style='color: {colour};'>{substring}</span></b>",
            out)
    return out
