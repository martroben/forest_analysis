# standard
import os
# external
import plotly
import polars as pl
from polars import col


##########
# Inputs #
##########

root_dir = "age_group_trends"
production_areas_path = "data/plot/production_areas.csv"
protected_areas_path = "data/plot/protected_areas.csv"
production_regeneration_cutting_path = "data/plot/production_regeneration_cutting.csv"
protected_regeneration_cutting_path = "data/plot/protected_regeneration_cutting.csv"

plot_save_path = "metsamaa_pindala_muutus.png"

non_age_group_fields = ["YEAR", "UNIT", "TYPE"]
regeneration_cutting_name = "uuendusraie"


#########################
# Functions and classes #
#########################

def rgb_to_hex(rgb: str) -> str:
    """
    Convert string in the form of 'rgb(10, 20, 30)' to a hex string.
    """
    rgb_components = [int(x.strip()) for x in rgb.strip("rgb()").split(",")]
    hex = "#{0:02x}{1:02x}{2:02x}".format(*rgb_components)
    return hex


#############
# Read data #
#############

production_areas = pl.read_csv(
    os.path.join(root_dir, production_areas_path),
    encoding="utf-8",
    separator=","
)
protected_areas = pl.read_csv(
    os.path.join(root_dir, protected_areas_path),
    encoding="utf-8",
    separator=","
)
production_regeneration_cutting = pl.read_csv(
    os.path.join(root_dir, production_regeneration_cutting_path),
    encoding="utf-8",
    separator=","
)
protected_regeneration_cutting = pl.read_csv(
    os.path.join(root_dir, protected_regeneration_cutting_path),
    encoding="utf-8",
    separator=","
)

production_areas_dict = production_areas.to_dict(as_series=False)
protected_areas_dict = protected_areas.to_dict(as_series=False)
production_regeneration_cutting_dict = production_regeneration_cutting.to_dict(as_series=False)
protected_regeneration_cutting_dict = protected_regeneration_cutting.to_dict(as_series=False)


###############
# Set colours #
###############

# plotly colourscale names: https://plotly.com/python/builtin-colorscales/
protected_colorscale = "Darkmint"
production_colorscale = "algae"
regeneration_colour = "#C35B00"

n_age_groups = max(
    len([key for key in production_areas_dict.keys() if key not in non_age_group_fields]),
    len([key for key in protected_areas_dict.keys() if key not in non_age_group_fields])
)

protected_colours_rgb = plotly.colors.sample_colorscale(
    protected_colorscale,
    [i / n_age_groups for i in range(1, n_age_groups + 1)]
)
production_colours_rgb = plotly.colors.sample_colorscale(
    production_colorscale,
    [i / n_age_groups for i in range(1, n_age_groups + 1)]
)

protected_colours = [rgb_to_hex(colour) for colour in protected_colours_rgb]
production_colours = [rgb_to_hex(colour) for colour in production_colours_rgb]


################
# Prepare data #
################

plot_data = []

# Add protected areas
protected_areas_data = {key: value for key, value in protected_areas_dict.items() if key not in non_age_group_fields}
protected_areas_type = protected_areas_dict["TYPE"][0]

for i, (age_group, areas) in enumerate(protected_areas_data.items()):
    plot_data += [
        plotly.graph_objects.Bar(
            x=protected_areas_dict["YEAR"],
            y=areas,
            name=age_group,
            offsetgroup=protected_areas_type,
            marker_color=protected_colours[i],
            showlegend=False
        )
    ]

# Add protected areas regeneration cutting
plot_data += [
    plotly.graph_objects.Bar(
        x=protected_regeneration_cutting_dict["YEAR"],
        y=protected_regeneration_cutting_dict["AREA"],
        name=regeneration_cutting_name,
        offsetgroup=protected_areas_type,
        marker_color=regeneration_colour,
        showlegend=False
    )
]

# Add production areas
production_areas_data = {key: value for key, value in production_areas_dict.items() if key not in non_age_group_fields}
production_areas_years = production_areas_dict["YEAR"]
production_areas_type = production_areas_dict["TYPE"][0]

for i, (age_group, areas) in enumerate(production_areas_data.items()):
    plot_data += [
        plotly.graph_objects.Bar(
            x=production_areas_dict["YEAR"],
            y=areas,
            name=age_group,
            offsetgroup=production_areas_type,
            marker_color=production_colours[i],
            showlegend=False
        )
    ]

# Add production areas regeneration cutting
plot_data += [
    plotly.graph_objects.Bar(
        x=production_regeneration_cutting_dict["YEAR"],
        y=production_regeneration_cutting_dict["AREA"],
        name=regeneration_cutting_name,
        offsetgroup=production_areas_type,
        marker_color=regeneration_colour,
        showlegend=False
    )
]


################
# Setup legend #
################

legend_colorscale = "Greys"

age_group_names = sorted(list(set(
    [key for key in production_areas_dict.keys() if key not in non_age_group_fields] + 
    [key for key in protected_areas_dict.keys() if key not in non_age_group_fields]))
)
age_group_colours_rgb = plotly.colors.sample_colorscale(
    legend_colorscale,
    [i / len(age_group_names) for i in range(1, len(age_group_names) + 1)]
)

legend_names = age_group_names + [regeneration_cutting_name]
legend_colours = [rgb_to_hex(colour) for colour in age_group_colours_rgb] + [regeneration_colour]

for name, colour in zip(legend_names, legend_colours):
    print(name, colour)
    # Add a dummy traces to control the legend
    plot_data += [
        plotly.graph_objects.Bar(
            x=[None], y=[None],
            name=name,
            marker_color=colour,
            showlegend=True
        )
    ]


#################
# Create layout #
#################

title_protected_colour = rgb_to_hex(plotly.colors.sample_colorscale(protected_colorscale, 0.7)[0])
title_production_colour = rgb_to_hex(plotly.colors.sample_colorscale(production_colorscale, 0.8)[0])

plot_title_html = f"<b><span style='color: {title_protected_colour};'>Mittemajandatava</span></b> ja <b><span style='color: {title_production_colour};'>majandatava</span></b> metsamaa pindalad vanusegruppide kaupa"
x_axis_title = "Aasta"
y_axis_title = "pindala (tuhat ha)"
source_annotation = "source: https://github.com/martroben/forest_analysis/tree/main/age_group_trends"

plot_layout = plotly.graph_objects.Layout(
    barmode="stack",
    bargroupgap=0.1,
    bargap=0.1,
    height=1300,
    width=3600,
    plot_bgcolor="white",
    title={
        "text": plot_title_html,
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
            "text": "Vanusegrupid:",
            "font": {"size": 28}
        }
    },
    annotations=[
        {
            "text": source_annotation,
            "xref": "paper",
            "yref": "paper",
            "x": 0,
            "y": -0.1,
            "showarrow": False,
            "font": {"size": 20},
            "align": "left"
        }
    ]
)

#############
# Save plot #
#############

figure = plotly.graph_objects.Figure(plot_data, plot_layout)

plot_save_path_full = os.path.join(root_dir, plot_save_path)
plotly.io.write_image(figure, plot_save_path_full, format="png")
