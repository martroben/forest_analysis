# standard
import re
# external
import plotly
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


def get_legend_traces(names: list[str], colours: list[str]) -> list[plotly.graph_objects.Bar]:
    """
    Get dummy traces to control the plot legend.
    """
    traces = []
    for name, colour in zip(names, colours):
        traces += [
            plotly.graph_objects.Bar(
                x=[None], y=[None],
                name=name,
                marker_color=colour,
                showlegend=True
            )
        ]
    return traces


def get_area_traces(type_name: str, years: list[int], areas_by_age_group: dict[str, list], colours_by_age_group: dict[str: str]) -> list[plotly.graph_objects.Bar]:
    """
    Get traces for area data.
    """
    traces = []
    for age_group, areas in areas_by_age_group.items():
        traces += [
            plotly.graph_objects.Bar(
                x=years,
                y=areas,
                name=age_group,
                offsetgroup=type_name,
                marker_color=colours_by_age_group[age_group],
                showlegend=False
            )
        ]
    return traces


def get_layout(title: str, x_axis_title: str, y_axis_title: str, legend_title: str, source: str) -> plotly.graph_objects.Layout:
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
            "dtick": 1,                     # Show label for every year
            "tickfont": {"size": 24}
        },
        yaxis={
            "gridcolor": "gray",
            "tickfont": {"size": 24},
            "dtick": 500,                   # Major gridlines
            "minor": {                      # Minor gridlines
                "dtick": 100,  
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
            "pad": 20,                      # Axis label padding
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


def apply_colour_to_substring(string: str, substring: str, colour: str) -> str:
    """
    Apply HTML bold + colour formatting to a substring of the input string.
    """
    if not substring in string:
        return string
    if f'>{substring}<' in string:
        # Skip if formatting is already applied
        return string
    out = re.sub(
        fr'\b{substring}\b',
        fr"<b><span style='color: {colour};'>{substring}</span></b>",
        string)
    return out


def get_figure(traces: list[plotly.graph_objects.Bar], layout: plotly.graph_objects.Layout) -> plotly.graph_objects.Figure:
    return plotly.graph_objects.Figure(traces, layout)


def save_plot(figure: plotly.graph_objects.Figure, path: str) -> None:
    plotly.io.write_image(figure, path, format="png")
