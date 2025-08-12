from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"

LOGOS = [
    ASSETS_DIR / "tsrc.jpg",
    ASSETS_DIR / "third_sector_database_logo.png",
    ASSETS_DIR / "ESRC.png",
    ASSETS_DIR / "gradel_institute.png",
]


def display() -> None:
    """Build the sidebar for the Streamlit app."""

    st.sidebar.title("Procurement Dashboard")

    logo_columns = st.sidebar.columns([0.6, 0.4])
    logo_columns[0].image(LOGOS[0])
    logo_columns[1].image(LOGOS[1])

    st.sidebar.image(LOGOS[2], use_container_width=True)
    st.sidebar.image(LOGOS[3], use_container_width=True)