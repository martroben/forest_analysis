import os
from pathlib import Path
import sys
import subprocess
# external
import tqdm


################
# Translations #
################

TRANSLATION_MAP = {
    "Selguseta ala": "renewal_not_complete",
    "Lage ala": "no_trees",
    "Kokku": "all",
    "Haab": "aspen",
    "Kask": "birch",
    "Sanglepp": "black_alder",
    "Hall lepp": "grey_alder",
    "Teised": "other",
    "Mänd": "pine",
    "Kuusk": "spruce",
    "all": "kokku",
    "aspen": "haab",
    "birch": "kask",
    "black_alder": "sanglepp",
    "grey_alder": "hall_lepp",
    "other": "teised",
    "pine": "mänd",
    "spruce": "kuusk",
    "RMK": "state_forest_management_centre",
    "Majandatav metsamaa": "production_forest",
    "Mittemajandatavad metsad": "protected_forest",
    "Kogu metsamaa": "all"
}


##################
# Prepare inputs #
##################

ROOT_DIR_PATH = "age_pyramid"

# 01
input_for_01_clean_area_by_age_group = {
    "ROOT_DIR_PATH": ROOT_DIR_PATH,

    # get raw data from Estonian National Forest Inventory tableau data
    # https://tableau.envir.ee/views/SMI/data/raw/17Vanuseklassidaegrida?%3Aembed=y > click on table heading > "View data..." > "Download"
    "AGE_GROUP_RAW_PATHS": """
        data/raw/17 Vanuseklassid aegrida tabel_data_all_all.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_aspen_all.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_birch_all.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_black_alder_all.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_grey_alder_all.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_other_all.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_pine_all.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_spruce_all.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_all_production.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_aspen_production.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_birch_production.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_black_alder_production.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_grey_alder_production.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_other_production.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_pine_production.csv,
        data/raw/17 Vanuseklassid aegrida tabel_data_spruce_production.csv
    """,
    "SAVE_PATH": "data/clean/area_by_age_group.csv"
}

# 02
input_for_02_clean_area_by_quality_class = {
    "ROOT_DIR_PATH": ROOT_DIR_PATH,

    # get raw data from Estonian National Forest Inventory tableau data
    # https://tableau.envir.ee/views/SMI/14Boniteediklassid?%3Aembed=y > click on table heading > "View data..." > "Download"
    "QUALITY_CLASS_RAW_PATHS": """
        data/raw/14 Boniteediklassid tabel_data_production_1999.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2000.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2001.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2002.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2003.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2004.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2005.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2006.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2007.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2008.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2009.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2010.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2011.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2012.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2013.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2014.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2015.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2016.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2017.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2018.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2019.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2020.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2021.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2022.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2023.csv,
        data/raw/14 Boniteediklassid tabel_data_production_2024.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_1999.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2000.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2001.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2002.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2003.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2004.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2005.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2006.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2007.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2008.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2009.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2010.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2011.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2012.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2013.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2014.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2015.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2016.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2017.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2018.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2019.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2020.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2021.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2022.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2023.csv,
        data/raw/14 Boniteediklassid tabel_data_protected_2024.csv
    """,

    "SAVE_PATH": "data/clean/area_by_quality_class.csv"
}

# 03
input_for_03_clean_maturity_ages = {
    "ROOT_DIR_PATH": ROOT_DIR_PATH,
    "SAVE_PATH": "data/clean/maturity_age.csv"
}

# 04
input_for_04_get_optimal_age_pyramid_areas = {
    "ROOT_DIR_PATH": ROOT_DIR_PATH,
    "AREA_BY_QUALITY_CLASS_DATA_PATH": "data/clean/area_by_quality_class.csv",
    "AREA_BY_AGE_GROUP_DATA_PATH": "data/clean/area_by_age_group.csv",
    "MATURITY_AGE_DATA_PATH": "data/clean/maturity_age.csv",
    "SAVE_PATH": "data/clean/optimal_age_pyramid_areas.csv",

    # Proportion of the remaining mature forest cut every year
    "STANDARD_ANNUAL_MATURE_CUT_PROPORTION": "0.055",
    # Proportion of non-renewed (production) area
    "STANDARD_NON_RENEWED_PROPORTION": "0.09",
    # Ensures that the saved areas include at least a minimum number of age groups
    "MINIMUM_TOP_AGE": "131",

    # Default maturity ages to use when no legal maturity age is set
    "ASPEN_DEFAULT_MATURITY_AGE": "30",
    "BLACK_ALDER_DEFAULT_MATURITY_AGE": "30",
    "GREY_ALDER_DEFAULT_MATURITY_AGE": "30"
}

# 05
input_for_05_plot_optimal_age_pyramid_1 = {
    "ROOT_DIR_PATH": ROOT_DIR_PATH,
    "YEAR": "2024",
    "OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH": "data/clean/optimal_age_pyramid_areas.csv",
    "SPECIES": "aspen",
    "QUALITY_CLASSES": "1A",
    "MANAGED_BY": "state_forest_management_centre, other",
    "PLOT_SUBTITLE": "Haab IA | kiire kasv, madal raievanus",
    "ANNOTATIONS": (
        "<u>github.com/martroben/forest_analysis/tree/main/age_pyramid/</u>"
        "<br>"
        "CC-BY license: Mart Roben"
    ),
    "SAVE_PATH": "result/optimaalne/optimaalne_vanusepüramiid_haab_IA.png"
}

input_for_05_plot_optimal_age_pyramid_2 = {
    "ROOT_DIR_PATH": ROOT_DIR_PATH,
    "YEAR": "2024",
    "OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH": "data/clean/optimal_age_pyramid_areas.csv",
    "SPECIES": "pine",
    "QUALITY_CLASSES": "5",
    "MANAGED_BY": "state_forest_management_centre, other",
    "PLOT_SUBTITLE": "Mänd V | aeglane kasv, kõrge raievanus",
    "ANNOTATIONS": (
        "<u>github.com/martroben/forest_analysis/tree/main/age_pyramid/</u>"
        "<br>"
        "CC-BY license: Mart Roben"
    ),
    "SAVE_PATH": "result/optimaalne/optimaalne_vanusepüramiid_mänd_V.png"
}

input_for_05_plot_optimal_age_pyramid_3 = {
    "ROOT_DIR_PATH": ROOT_DIR_PATH,
    "YEAR": "2024",
    "OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH": "data/clean/optimal_age_pyramid_areas.csv",
    "SPECIES": "spruce, pine, birch, aspen, grey_alder, black_alder, other",
    "QUALITY_CLASSES": "5A-5B, 5, 4, 3, 2, 1A, 1",
    "MANAGED_BY": "state_forest_management_centre, other",
    "PLOT_SUBTITLE": "Kõik puuliigid ja boniteediklassid kokku",
    "ANNOTATIONS": (
        "<u>github.com/martroben/forest_analysis/tree/main/age_pyramid/</u>"
        "<br>"
        "CC-BY license: Mart Roben"
    ),
    "SAVE_PATH": "result/optimaalne/optimaalne_vanusepüramiid_kokku.png"
}

# 06
years = list(range(1999, 2024 + 1))

# Can be several comma separated values
# spruce, pine, birch, aspen, grey_alder, black_alder, other
all_species = ["spruce", "pine", "birch", "aspen", "grey_alder", "black_alder", "other"]
species_combinations = [
    "spruce",
    "pine",
    "birch",
    "aspen",
    "grey_alder",
    "black_alder",
    "other",
    ",".join(all_species)
]

inputs_for_06_plot_real_age_pyramid = []
for species in species_combinations:
    if not set(all_species) - set(species.split(",")):
        species_title_name = "kõik_liigid_kokku"
    else:
        species_title_name = "_".join([TRANSLATION_MAP[item.strip()] for item in species.split(",")])

    for year in years:
        inputs_for_06_plot_real_age_pyramid += [{
            "ROOT_DIR_PATH": ROOT_DIR_PATH,
            "AREA_BY_AGE_GROUP_DATA_PATH": "data/clean/area_by_age_group.csv",
            "OPTIMAL_AGE_PYRAMID_AREAS_DATA_PATH": "data/clean/optimal_age_pyramid_areas.csv",
            "ANNOTATIONS": (
                "<u>github.com/martroben/forest_analysis/tree/main/age_pyramid/</u>"
                "<br>"
                "CC-BY license: Mart Roben"
            ),
            "YEAR": str(year),
            "SPECIES": species,
            "PLOT_TITLE": f'Vanusepüramiid {year} - {species_title_name.replace("_", " ")}',
            "SAVE_PATH": f'result/{species_title_name}/vanusepüramiid_{species_title_name}_{year}.png'
        }]


#########################
# Functions and classes #
#########################

def run_script(script_path: Path, env_variables: dict) -> None:
    """
    Run a Python script file with given environment variables.
    """
    env = os.environ.copy()
    env.update(env_variables)
    subprocess.run(
        [sys.executable, script_path],
        check=True,
        env=env
    )


####################
# Orchestrate runs #
####################

run_script(
    script_path=Path(ROOT_DIR_PATH) / "src/01_clean_area_by_age_group.py",
    env_variables=input_for_01_clean_area_by_age_group
)

run_script(
    script_path=Path(ROOT_DIR_PATH) / "src/02_clean_area_by_quality_class.py",
    env_variables=input_for_02_clean_area_by_quality_class
)

run_script(
    script_path=Path(ROOT_DIR_PATH) / "src/03_clean_maturity_ages.py",
    env_variables=input_for_03_clean_maturity_ages
)

run_script(
    script_path=Path(ROOT_DIR_PATH) / "src/04_get_optimal_age_pyramid_areas.py",
    env_variables=input_for_04_get_optimal_age_pyramid_areas
)

run_script(
    script_path=Path(ROOT_DIR_PATH) / "src/05_plot_optimal_age_pyramid.py",
    env_variables=input_for_05_plot_optimal_age_pyramid_1
)

run_script(
    script_path=Path(ROOT_DIR_PATH) / "src/05_plot_optimal_age_pyramid.py",
    env_variables=input_for_05_plot_optimal_age_pyramid_2
)

run_script(
    script_path=Path(ROOT_DIR_PATH) / "src/05_plot_optimal_age_pyramid.py",
    env_variables=input_for_05_plot_optimal_age_pyramid_3
)

for env_variables in tqdm.tqdm(inputs_for_06_plot_real_age_pyramid, desc="plotting age pyramids"):
    run_script(
        script_path=Path(ROOT_DIR_PATH) / "src/06_plot_real_age_pyramid.py",
        env_variables=env_variables
    )
