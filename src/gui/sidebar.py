"""Sidebar for the app."""

import base64
from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"

ABOUT_FILE = ASSETS_DIR / "about.md"
PRIVACY_FILE = ASSETS_DIR / "privacy.md"

LOGOS = [
    # ASSETS_DIR / "oxford_logo.png",
    [ASSETS_DIR / "tsrc_square.jpg", "https://www.birmingham.ac.uk/research/tsrc"],
    [ASSETS_DIR / "third_sector_database_logo.png", "https://uk-third-sector-database.github.io/"],
    [ASSETS_DIR / "2024_oxrse_square.png", "https://www.rse.ox.ac.uk"],
    [ASSETS_DIR / "gradel_institute.png", "https://www.gradelinstituteofcharity.co.uk/"],
    [ASSETS_DIR / "ESRC.png", "https://www.ukri.org/councils/esrc/"],
]


def image_with_link(image_path: Path, link_url: str, width: int = 100) -> None:
    """Render an image as a clickable link in Streamlit."""
    with open(image_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    st.markdown(
        f'<a href="{link_url}" target="_blank">'
        f'<img src="data:image/png;base64,{b64}" width="{width}">'
        f"</a>",
        unsafe_allow_html=True,
    )


def display() -> None:
    """Build the sidebar for the Streamlit app."""

    st.sidebar.header("UK Third Sector Database")

    logo_columns = st.sidebar.columns(3)
    with logo_columns[0]:
        image_with_link(LOGOS[0][0], LOGOS[0][1])
    with logo_columns[1]:
        image_with_link(LOGOS[1][0], LOGOS[1][1])
    with logo_columns[2]:
        image_with_link(LOGOS[2][0], LOGOS[2][1])

    logo_columns = st.sidebar.columns(2)
    with logo_columns[0]:
        image_with_link(LOGOS[3][0], LOGOS[3][1])
    with logo_columns[1]:
        image_with_link(LOGOS[4][0], LOGOS[4][1])

    with st.sidebar.expander("Project information", expanded=False):
        with st.popover("About the project"):
            st.markdown(ABOUT_FILE.read_text(encoding="utf-8"))
        with st.popover("Privacy policy"):
            st.markdown(PRIVACY_FILE.read_text(encoding="utf-8"))

        with st.popover("Resources"):
            st.link_button("Project GitHub page", "https://uk-third-sector-database.github.io/")
            st.link_button("Raw spine files", "https://uk-third-sector-database.github.io/data/")
            st.link_button("How to use the dataset", "https://uk-third-sector-database.github.io/")

    st.sidebar.divider()
