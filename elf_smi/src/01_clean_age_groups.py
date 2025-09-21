# standard
import os
import sys
# external
import polars as pl
from polars import col
# local
src_path = os.path.abspath("elf_smi/src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import clean


################
# Translations #
################

TRANSLATION_MAP = {
    "Selguseta ala": "renewal not complete",
    "Lage ala": "clearcut",
    "Kokku": "all",
    "Haab": "aspen",
    "Kask": "birch",
    "Sanglepp": "black alder",
    "Hall lepp": "grey alder",
    "Teised": "other",
    "Mänd": "pine",
    "Kuusk": "spruce",
    "all": "kokku",
    "aspen": "haab",
    "birch": "kask",
    "black alder": "sanglepp",
    "grey alder": "hall_lepp",
    "other": "teised",
    "pine": "mänd",
    "spruce": "kuusk"
}


#########
# Input #
#########

ROOT_DIR_PATH = "elf_smi"

# --[ Load paths

# https://tableau.envir.ee/views/SMI/28Raieaegrida?%3Aembed=y > click on table heading > "View data..." > "Download"
REGENERATION_CUTTING_RAW_PATHS = {
    "all":          "data/raw/28 Raie aegrida tabel_data_all.csv"
}

# raw data load paths
# get raw data from Estonian National Forest Inventory tableau data
# https://tableau.envir.ee/views/SMI/17Vanuseklassidaegrida?%3Aembed=y > click on table heading > "View data..." > "Download"
AGE_GROUP_RAW_PATHS = {
    "all":          "data/raw/17 Vanuseklassid aegrida tabel_data_all_all.csv",
    "aspen":        "data/raw/17 Vanuseklassid aegrida tabel_data_aspen_all.csv",
    "birch":        "data/raw/17 Vanuseklassid aegrida tabel_data_birch_all.csv",
    "black alder":  "data/raw/17 Vanuseklassid aegrida tabel_data_black_alder_all.csv",
    "grey alder":   "data/raw/17 Vanuseklassid aegrida tabel_data_grey_alder_all.csv",
    "other":        "data/raw/17 Vanuseklassid aegrida tabel_data_other_all.csv",
    "pine":         "data/raw/17 Vanuseklassid aegrida tabel_data_pine_all.csv",
    "spruce":       "data/raw/17 Vanuseklassid aegrida tabel_data_spruce_all.csv"
}
AGE_GROUP_PRODUCTION_RAW_PATHS = {
    "all":          "data/raw/17 Vanuseklassid aegrida tabel_data_all_production.csv",
    "aspen":        "data/raw/17 Vanuseklassid aegrida tabel_data_aspen_production.csv",
    "birch":        "data/raw/17 Vanuseklassid aegrida tabel_data_birch_production.csv",
    "black alder":  "data/raw/17 Vanuseklassid aegrida tabel_data_black_alder_production.csv",
    "grey alder":   "data/raw/17 Vanuseklassid aegrida tabel_data_grey_alder_production.csv",
    "other":        "data/raw/17 Vanuseklassid aegrida tabel_data_other_production.csv",
    "pine":         "data/raw/17 Vanuseklassid aegrida tabel_data_pine_production.csv",
    "spruce":       "data/raw/17 Vanuseklassid aegrida tabel_data_spruce_production.csv"
}

# --[ Save paths
REGENERATION_CUTTING_SAVE_PATH = "data/clean/regeneration_cutting.csv"
AGE_GROUP_SAVE_PATH = "data/clean/age_group.csv"


###################################
# Clean regeneration cutting data #
###################################

regeneration_cutting = pl.DataFrame()
# Load data by species
for dominant_species, path in REGENERATION_CUTTING_RAW_PATHS.items():
    # Read
    with open(os.path.join(ROOT_DIR_PATH, path), encoding="utf-8") as read_file:
        regeneration_cutting_raw = pl.read_csv(
            read_file,
            separator=";"
        )
    # Add default values
    # Regeneration cutting does not have age group or type (production/protected) info. Denoting both as "all" (combined data).
    regeneration_cutting_defaults = (
        regeneration_cutting_raw
        .with_columns(
            TYPE=None,
            DOMINANT_SPECIES=pl.lit("all"),
            AGE_GROUP=None
        )
    )
    # Clean
    regeneration_cutting_clean_by_species = clean.clean_regeneration_cutting_data(regeneration_cutting_defaults)
    # Validate
    is_unique_species = clean.is_unique_value(
        regeneration_cutting_clean_by_species,
        field="DOMINANT_SPECIES"
    )
    species_values = regeneration_cutting_clean_by_species["DOMINANT_SPECIES"]
    is_species_match_input = dominant_species in species_values
    if not all([is_unique_species, is_species_match_input]):
        raise ValueError(f'Input tree species "{dominant_species}" for path "{path}" does not match the tree species values in the actual data: {species_values.unique().to_list()}')
    
    # Add to existing
    regeneration_cutting = pl.concat([
        regeneration_cutting,
        regeneration_cutting_clean_by_species
    ])

# Save
regeneration_cutting_save_path = os.path.join(ROOT_DIR_PATH, REGENERATION_CUTTING_SAVE_PATH)
os.makedirs(
    os.path.dirname(regeneration_cutting_save_path),
    exist_ok=True)

with open(regeneration_cutting_save_path, "w", encoding="utf-8") as save_file:
    regeneration_cutting.write_csv(
        save_file,
        separator=","
    )


########################
# Clean age group data #
########################

age_group_clean = pl.DataFrame()
# Load data by species
for species, path in AGE_GROUP_RAW_PATHS.items():
    # Read
    with open(os.path.join(ROOT_DIR_PATH, path), encoding="utf-8") as read_file:
        age_group_raw = pl.read_csv(
            read_file,
            separator=";"
        )
    age_group_defaults = (
        age_group_raw
        .with_columns(
            TYPE=pl.lit("all")
        )
    )
    # Clean
    age_group_clean_by_species = clean.clean_age_group_data(age_group_defaults, TRANSLATION_MAP)
    # Validate
    is_unique_species = clean.is_unique_value(
        age_group_clean_by_species,
        field="DOMINANT_SPECIES"
    )
    species_values = age_group_clean_by_species["DOMINANT_SPECIES"]
    is_species_match_input = (species in species_values)
    if not all([is_unique_species, is_species_match_input]):
        raise ValueError(f'Input tree species "{species}" for path "{path}" does not match the tree species values in the actual data: {species_values.unique().to_list()}')
    # Add to existing
    age_group_clean = pl.concat([
        age_group_clean,
        age_group_clean_by_species
    ])


age_group_production_clean = pl.DataFrame()
# Load data by species
for species, path in AGE_GROUP_PRODUCTION_RAW_PATHS.items():
    # Read
    with open(os.path.join(ROOT_DIR_PATH, path), encoding="utf-8") as read_file:
        age_group_production_raw = pl.read_csv(
            read_file,
            separator=";"
        )
    age_group_production_defaults = (
        age_group_production_raw
        .with_columns(
            TYPE=pl.lit("production")
        )
    )
    # Clean
    age_group_production_clean_by_species = clean.clean_age_group_data(age_group_production_defaults, TRANSLATION_MAP)
    # Validate
    is_unique_species = clean.is_unique_value(
        age_group_production_clean_by_species,
        field="DOMINANT_SPECIES"
    )
    species_values = age_group_production_clean_by_species["DOMINANT_SPECIES"]
    is_species_match_input = (species in species_values)
    if not all([is_unique_species, is_species_match_input]):
        raise ValueError(f'Input tree species for path {path} ({species}) does not match the tree species values in input data: {species_values}')
    # Add to existing
    age_group_production_clean = pl.concat([
        age_group_production_clean,
        age_group_production_clean_by_species
    ])

age_group = clean.combine_all_and_production_data(age_group_clean, age_group_production_clean)

# Validate species totals
age_group_areas_by_species = (
    age_group
    .filter(col("DOMINANT_SPECIES") != "all")
    .select(col("AREA"))
    .to_series()
    .to_list()
)
age_group_areas_by_totals = (
    age_group
    .filter(col("DOMINANT_SPECIES") == "all")
    .select(col("AREA"))
    .to_series()
    .to_list()
)
if abs(sum(age_group_areas_by_species) - sum(age_group_areas_by_totals)) > 1:
    raise ValueError(f'Total area by individual species ({age_group_areas_by_species} kha) does not match the total area by the "all" species rows ({age_group_areas_by_totals}) kha')

# Save
age_group_save_path = os.path.join(ROOT_DIR_PATH, AGE_GROUP_SAVE_PATH)
os.makedirs(
    os.path.dirname(age_group_save_path),
    exist_ok=True)

with open(age_group_save_path, "w", encoding="utf-8") as save_file:
    age_group.write_csv(
        save_file,
        separator=","
    )
