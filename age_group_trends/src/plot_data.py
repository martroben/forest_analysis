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

plot_save_path = "metsamaa_pindala_muutus.png"


#############
# Read data #
#############

production_areas = pl.read_csv(
    os.path.join(root_dir, production_areas_path),
    encoding="utf-8",
    separator=",")

protected_areas = pl.read_csv(
    os.path.join(root_dir, protected_areas_path),
    encoding="utf-8",
    separator=","
)

production_areas_dict = production_areas.to_dict(as_series=False)
protected_areas_dict = protected_areas.to_dict(as_series=False)


################
# Prepare data #
################

plot_data = []

# Add protected areas data
protected_areas_years = protected_areas_dict["YEAR"]

if len(set(protected_areas_dict["TYPE"])) != 1:
    raise ValueError("Multiple types found in protected areas data.")
protected_areas_type = protected_areas_dict["TYPE"][0]

for key, value in protected_areas_dict.items():
    if key in ["YEAR", "TYPE", "UNIT"]:
        continue

    plot_data += [
        plotly.graph_objects.Bar(
            x=protected_areas_years,
            y=value,
            name=key,
            offsetgroup=protected_areas_type
        )
    ]

# Add production areas data
production_areas_years = production_areas_dict["YEAR"]

if len(set(production_areas_dict["TYPE"])) != 1:
    raise ValueError("Multiple types found in production areas data.")
production_areas_type = production_areas_dict["TYPE"][0]

for key, value in production_areas_dict.items():
    if key in ["YEAR", "TYPE", "UNIT"]:
        continue

    plot_data += [
        plotly.graph_objects.Bar(
            x=production_areas_years,
            y=value,
            name=key,
            offsetgroup=production_areas_type
        )
    ]


#################
# Create layout #
#################

plot_layout = plotly.graph_objects.Layout(
    title="Majandatava ja mittemajandatava metsamaa pindala",
    xaxis_title="Aasta",
    yaxis_title="pindala (tuhat ha)",
    legend_title="Vanusegrupp",
    # width=3000,
    # height=1500,
    # margin=dict(l=100, r=100, t=100, b=100),
    # font=dict(size=18)
    barmode="stack"
)


#############
# Save plot #
#############

figure = plotly.graph_objects.Figure(plot_data, plot_layout)
plotly.io.write_image(figure, plot_save_path, format="png", scale=2)
