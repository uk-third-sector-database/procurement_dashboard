"""Shared constants and path helpers across modules."""
from pathlib import Path

# Root of the repository, independent of CWD
# src/utilities/shared.py -> utilities (0) -> src (1) -> repo root (2)
ROOT = Path(__file__).resolve().parents[2]

# Assets
ASSETS_DIR = ROOT / "assets"

ABOUT_FILE = ASSETS_DIR / "about.md"
PRIVACY_FILE = ASSETS_DIR / "privacy.md"

LOGOS = [
    # [ASSETS_DIR / "oxford_logo.png", "https://www.ox.ac.uk"],
    [ASSETS_DIR / "tsrc_square.jpg", "https://www.birmingham.ac.uk/research/tsrc"],
    [ASSETS_DIR / "third_sector_database_logo.png",
     "https://uk-third-sector-database.github.io/"],
    [ASSETS_DIR / "2024_oxrse_square.png", "https://www.rse.ox.ac.uk"],
    [ASSETS_DIR / "gradel_institute.png",
     "https://www.gradelinstituteofcharity.co.uk/"],
    [ASSETS_DIR / "ESRC.png", "https://www.ukri.org/councils/esrc/"],
]

# Data
DATA_DIR = ROOT / "data" / "processed"

# Single parquet file containing your dataset
FILEPATH = DATA_DIR / "dataset.parquet"

# Shapefile (adjust subdirectory/name if needed)
SHAPE_FILE = (
    ASSETS_DIR
    / "NUTS_RG_01M_2021_4326_shp"
    / "NUTS_RG_01M_2021_4326_shp.shp"
)

NULL_TEXT = "Not specified"
