""" Shared constants and functions across modules."""
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"

ABOUT_FILE = ASSETS_DIR / "about.md"
PRIVACY_FILE = ASSETS_DIR / "privacy.md"

FILEPATH = Path(__file__).parent.parent.parent / "data" / "processed" / "dataset.parquet"

LOGOS = [
    # ASSETS_DIR / "oxford_logo.png",
    [ASSETS_DIR / "tsrc_square.jpg", "https://www.birmingham.ac.uk/research/tsrc"],
    [ASSETS_DIR / "third_sector_database_logo.png", "https://uk-third-sector-database.github.io/"],
    [ASSETS_DIR / "2024_oxrse_square.png", "https://www.rse.ox.ac.uk"],
    [ASSETS_DIR / "gradel_institute.png", "https://www.gradelinstituteofcharity.co.uk/"],
    [ASSETS_DIR / "ESRC.png", "https://www.ukri.org/councils/esrc/"],
]

SHAPE_FILE = ASSETS_DIR / "NUTS_RG_01M_2021_4326_shp" / "NUTS_RG_01M_2021_4326_shp.shp"

NULL_TEXT = "Not specified"
