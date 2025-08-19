from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"

LOGOS = [
    ASSETS_DIR / "oxford_logo.png",
    ASSETS_DIR / "tsrc_square.jpg",
    ASSETS_DIR / "third_sector_database_logo.png",
    ASSETS_DIR / "2024_oxrse_square.svg",
    ASSETS_DIR / "gradel_institute.png",
    ASSETS_DIR / "ESRC.png",
]


def display() -> None:
    """Build the sidebar for the Streamlit app."""

    st.sidebar.title("Procurement Dashboard")

    logo_columns = st.sidebar.columns(4)
    logo_columns[0].image(LOGOS[0])
    logo_columns[1].image(LOGOS[1])
    logo_columns[2].image(LOGOS[2])
    logo_columns[3].image(LOGOS[3])
    logo_columns = st.sidebar.columns(2)
    logo_columns[0].image(LOGOS[4])
    logo_columns[1].image(LOGOS[5])
    