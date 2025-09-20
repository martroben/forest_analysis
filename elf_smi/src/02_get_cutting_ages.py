# standard
import os
# external
import polars as pl
from polars import col

##########
# Inputs #
##########

ROOT_DIR_PATH = "elf_smi"
AGE_GROUP_PATH = "data/clean/age_group.csv"
CUTTING_AGE_SAVE_PATH = "data/clean/cutting_age.csv"

CUTTING_AGE = {
    # Estimated ages of regeneration cuttings by tree species
    # https://www.riigiteataja.ee/akt/113062025014?leiaKehtiv
    "aspen": 40,
    "birch": 60,
    "black alder": 60,
    "grey alder": 30,
    "other": 90,
    "pine": 90,
    "spruce": 70
}


#############
# Load data #
#############

age_group_path = os.path.join(ROOT_DIR_PATH, AGE_GROUP_PATH)
with open(age_group_path, encoding="utf-8") as read_file:
    age_group_data = pl.read_csv(read_file)


####################
# Get cutting ages #
####################

# --[ strategy
# 1. Generate cutting ages data frame for single species using the data from CUTTING_AGE input
# 2. Calculate proportions of each species for each year in age group data
# 3. Calculate combined cutting age for all species for each year, using the cutting ages and proportions of each individual species
# 4. Combine the data for individual species and all species

cutting_age_single_species = (
    pl.DataFrame(CUTTING_AGE)
    .unpivot(
        variable_name="DOMINANT_SPECIES",
        value_name="CUTTING_AGE"
    )
    .with_columns(
        TYPE=pl.lit("production"),
        CUTTING_AGE=col("CUTTING_AGE").cast(pl.Float64)
    )
    .join(
        age_group_data,
        on=[
            col("DOMINANT_SPECIES"),
            col("TYPE")
        ],
        how="right"
    )
    .filter(
        col("DOMINANT_SPECIES") != "all"
    )
    .group_by(
        col("YEAR"),
        col("TYPE"),
        col("DOMINANT_SPECIES"),
        col("CUTTING_AGE")
    )
    .agg()
)
species_proportions = (
    age_group_data
    .filter(
        col("DOMINANT_SPECIES") != "all"
    )
    .group_by([
        col("DOMINANT_SPECIES"),
        col("YEAR"),
        col("TYPE")
    ])
    .agg(col("AREA").sum().alias("AREA"))
    .with_columns(
        PROPORTION=col("AREA") / pl.sum("AREA").over("YEAR", "TYPE")
    )
    .sort(col("YEAR"), col("TYPE"))
)
cutting_age_all_species = (
    species_proportions
    .join(
        cutting_age_single_species,
        on=[
            col("YEAR"),
            col("DOMINANT_SPECIES"),
            col("TYPE")
        ],
        how="left"
    )
    .with_columns(
        CUTTING_AGE_CONTRIBUTION=col("PROPORTION") * col("CUTTING_AGE")
    )
    # Add up cutting ages by tree species for each year to get an overall cutting age for all species
    .group_by(
        col("YEAR"),
        col("TYPE")
    )
    .agg(
        DOMINANT_SPECIES=pl.lit("all"),
        CUTTING_AGE=col("CUTTING_AGE_CONTRIBUTION").sum()
    )
)
cutting_age = (
    pl.concat([
        cutting_age_single_species,
        cutting_age_all_species
    ])
    .sort(
        col("YEAR"),
        col("DOMINANT_SPECIES"),
        col("TYPE")
    )
)


#############
# Save data #
#############

save_path = os.path.join(ROOT_DIR_PATH, CUTTING_AGE_SAVE_PATH)

os.makedirs(
    os.path.dirname(save_path),
    exist_ok=True)

with open(save_path, "w", encoding="utf-8") as save_file:
    cutting_age.write_csv(
        save_file,
        separator=",",
    )
