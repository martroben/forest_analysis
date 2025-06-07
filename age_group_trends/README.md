# Age Group Forest Analysis

This project analyzes Estonian forest areas by age groups using [Estonian National Forest Inventory](https://keskkonnaportaal.ee/et/teemad/mets/metsastatistika-sh-smi) data. It visualises the distribution between protected and production forests across different age categories.

## Data Sources
- Age group data: [Forest Age Classes](https://tableau.envir.ee/views/SMI/17Vanuseklassidaegrida?%3Aembed=y)
- Cutting areas: [Forest Cutting Statistics](https://tableau.envir.ee/views/SMI/28Raieaegrida?%3Aembed=y)

## Example Output
![Age group trends](/age_group_trends/metsamaa_pindala_muutus.png)

## Project Structure
```
.
├── README.md
├── data/
│   ├── raw/      # Source data files
│   ├── clean/    # Processed data
│   └── plot/     # Visualisation data
└── src/
    ├── clean_data.py         # Data cleaning
    ├── prepare_plot_data.py  # Data formatting
    └── plot_data.py          # Visualisation
```

## Installation

1. Clone and install dependencies:
```shell
git clone https://github.com/martroben/forest_analysis/

cd forest_analysis
pip install -r requirements.txt
```

2. Optional: Update source data
   - Download latest data from sources to `data/raw/`
   - Update filenames in `clean_data.py`

3. Generate visualisation:
```shell
python -m src/clean_data.py
python -m src/plot_data.py
python -m src/prepare_plot_data.py
```

## Libraries
- [`plotly`](https://plotly.com/python/) for visualisation
- [`polars`](https://pola.rs/) for data processing

## Limitations
- Production forest category also includes semi-restricted production areas. Source data does not allow for different grouping.
- Only regeneration cutting areas are included in analysis. Other types of cutting (thinning etc.) are not.
- Regeneration cutting statistics are only available from 2014 onwards.
