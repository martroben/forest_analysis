# standard
import os
from pathlib import Path
# external
import polars as pl


################
# Manual input #
################

ROOT_DIR_PATH = "age_pyramid"
SAVE_PATH = "data/clean/maturity_age.csv"


#############
# Env input #
#############

# Manual inputs act as defaults and can be overridden by env inputs
ROOT_DIR_PATH = os.getenv("ROOT_DIR_PATH", ROOT_DIR_PATH)
SAVE_PATH = os.getenv("SAVE_PATH", SAVE_PATH)


#####################
# Manual data input #
#####################

# http://www.zbi.ee/talkk/materjalid/TA%20LKK%20290508%20Rainer%20Kuuba.pdf p.28
# ? Takseerkaardi täitmise juhend. Eesti Metsakorralduskeskus 1994
MATURITY_AGES_1993_1998 = [
    # SPECIES       # QUALITY_CLASS     # MATURITY_AGE
    ("pine",        "1A",               90),
    ("pine",        "1",                90),
    ("pine",        "2",               100),
    ("pine",        "3",               120),
    ("pine",        "4",               130),
    ("pine",        "5",               140),
    ("pine",        "5A",              140),
    ("spruce",      "1A",               70),
    ("spruce",      "1",                80),
    ("spruce",      "2",                90),
    ("spruce",      "3",               100),
    ("spruce",      "4",               100),
    ("spruce",      "5",               100),
    ("spruce",      "5A",              100),
    ("birch",       "1A",               60),
    ("birch",       "1",                70),
    ("birch",       "2",                70),
    ("birch",       "3",                80),
    ("birch",       "4",                70),
    ("birch",       "5",                70),
    ("birch",       "5A",               70),
    ("aspen",       "1A",               50),
    ("aspen",       "1",                50),
    ("aspen",       "2",                50),
    ("aspen",       "3",                50),
    ("aspen",       "4",                50),
]

# https://www.riigiteataja.ee/akt/33469 §13 pt.4
MATURITY_AGES_1999_2006 = [
    ("pine",        "1A",              100),
    ("pine",        "1",               100),
    ("pine",        "2",               100),
    ("pine",        "3",               100),
    ("pine",        "4",               100),
    ("pine",        "5",               100),
    ("pine",        "5A",              100),
    ("spruce",      "1A",               80),
    ("spruce",      "1",                80),
    ("spruce",      "2",                80),
    ("spruce",      "3",                80),
    ("spruce",      "4",                80),
    ("spruce",      "5",                80),
    ("spruce",      "5A",               80),
    ("birch",       "1A",               70),
    ("birch",       "1",                70),
    ("birch",       "2",                70),
    ("birch",       "3",                70),
    ("birch",       "4",                70),
    ("birch",       "5",                70),
    ("birch",       "5A",               70),
    ("hardwood",    "1A",              100),
    ("hardwood",    "1",               100),
    ("hardwood",    "2",               100),
    ("hardwood",    "3",               100),
    ("hardwood",    "4",               100),
    ("hardwood",    "5",               100),
    ("hardwood",    "5A",              100)
]

# https://www.riigiteataja.ee/akt/12771900 §3 pt.3
MATURITY_AGES_2007_2017 = [
    # SPECIES       # QUALITY_CLASS     # MATURITY_AGE
    ("pine",        "1A",               90),
    ("pine",        "1",                90),
    ("pine",        "2",                90),
    ("pine",        "3",               100),
    ("pine",        "4",               110),
    ("pine",        "5",               120),
    ("pine",        "5A",              120),
    ("spruce",      "1A",               80),
    ("spruce",      "1",                80),
    ("spruce",      "2",                80),
    ("spruce",      "3",                90),
    ("spruce",      "4",                90),
    ("spruce",      "5",                90),
    ("spruce",      "5A",               90),
    ("birch",       "1A",               60),
    ("birch",       "1",                60),
    ("birch",       "2",                70),
    ("birch",       "3",                70),
    ("birch",       "4",                70),
    ("birch",       "5",                70),
    ("birch",       "5A",               70),
    ("aspen",       "1A",               30),
    ("aspen",       "1",                40),
    ("aspen",       "2",                40),
    ("aspen",       "3",                50),
    ("aspen",       "4",                50),
    ("black_alder", "1A",               60),
    ("black_alder", "1",                60),
    ("black_alder", "2",                60),
    ("black_alder", "3",                60),
    ("black_alder", "4",                60),
    ("black_alder", "5",                60),
    ("black_alder", "5A",               60),
    ("hardwood",    "1A",               90),
    ("hardwood",    "1",                90),
    ("hardwood",    "2",               100),
    ("hardwood",    "3",               110),
    ("hardwood",    "4",               120),
    ("hardwood",    "5",               130),
    ("hardwood",    "5A",              130)
]

# https://www.riigiteataja.ee/akt/130082017018 §3 pt.1^2
MATURITY_AGES_2018_ = [
    # SPECIES       # QUALITY_CLASS     # MATURITY_AGE
    ("pine",        "1A",               90),
    ("pine",        "1",                90),
    ("pine",        "2",                90),
    ("pine",        "3",               100),
    ("pine",        "4",               110),
    ("pine",        "5",               120),
    ("pine",        "5A",              120),
    ("spruce",      "1A",               60),
    ("spruce",      "1",                70),
    ("spruce",      "2",                80),
    ("spruce",      "3",                90),
    ("spruce",      "4",                90),
    ("spruce",      "5",                90),
    ("spruce",      "5A",               90),
    ("birch",       "1A",               60),
    ("birch",       "1",                60),
    ("birch",       "2",                70),
    ("birch",       "3",                70),
    ("birch",       "4",                70),
    ("birch",       "5",                70),
    ("birch",       "5A",               70),
    ("aspen",       "1A",               30),
    ("aspen",       "1",                40),
    ("aspen",       "2",                40),
    ("aspen",       "3",                50),
    ("aspen",       "4",                50),
    ("black_alder", "1A",               60),
    ("black_alder", "1",                60),
    ("black_alder", "2",                60),
    ("black_alder", "3",                60),
    ("black_alder", "4",                60),
    ("black_alder", "5",                60),
    ("black_alder", "5A",               60),
    ("hardwood",    "1A",               90),
    ("hardwood",    "1",                90),
    ("hardwood",    "2",               100),
    ("hardwood",    "3",               110),
    ("hardwood",    "4",               120),
    ("hardwood",    "5",               130),
    ("hardwood",    "5A",              130)
]


################
# Process data #
################

maturity_ages_1993_1998 = (
    pl.DataFrame(
        {"YEAR": list(range(1993, 1999))}
    )
    .join(
        pl.DataFrame(
            MATURITY_AGES_1993_1998,
            schema={
                "SPECIES": pl.String,
                "QUALITY_CLASS": pl.String,
                "MATURITY_AGE": pl.Int16
            },
            orient="row"
        ),
        how="cross"
    )
)

maturity_ages_1999_2006 = (
    pl.DataFrame(
        {"YEAR": list(range(1999, 2007))}
    )
    .join(
        pl.DataFrame(
            MATURITY_AGES_1999_2006,
            schema={
                "SPECIES": pl.String,
                "QUALITY_CLASS": pl.String,
                "MATURITY_AGE": pl.Int16
            },
            orient="row"
        ),
        how="cross"
    )
)

maturity_ages_2007_2017 = (
    pl.DataFrame(
        {"YEAR": list(range(2007, 2018))}
    )
    .join(
        pl.DataFrame(
            MATURITY_AGES_2007_2017,
            schema={
                "SPECIES": pl.String,
                "QUALITY_CLASS": pl.String,
                "MATURITY_AGE": pl.Int16
            },
            orient="row"
        ),
        how="cross"
    )
)

maturity_ages_2018_ = (
    pl.DataFrame(
        {"YEAR": list(range(2018, 2026))}
    )
    .join(
        pl.DataFrame(
            MATURITY_AGES_2018_,
            schema={
                "SPECIES": pl.String,
                "QUALITY_CLASS": pl.String,
                "MATURITY_AGE": pl.Int16
            },
            orient="row"
        ),
        how="cross"
    )
)

save_data = pl.concat([
    maturity_ages_1993_1998,
    maturity_ages_1999_2006,
    maturity_ages_2007_2017,
    maturity_ages_2018_
])


########
# Save #
########

save_path = Path(ROOT_DIR_PATH) / SAVE_PATH
save_path.parent.mkdir(parents=True, exist_ok=True)

with open(save_path, "w", encoding="utf-8") as save_file:
    save_data.write_csv(
        save_file,
        separator=","
    )
