import streamlit as st

LOGOS = [
    "./assets/tsrc.jpg",
    "./assets/third_sector_database_logo.png",
    "./assets/ESRC.png",
    "./assets/gradel_institute.png",
]


def display() -> None:
    """Build the sidebar for the Streamlit app."""

    st.sidebar.subheader("Procurement Dashboard")

    logo_columns = st.sidebar.columns([0.6, 0.4])
    logo_columns[0].image(LOGOS[0])
    logo_columns[1].image(LOGOS[1])

    st.sidebar.image(LOGOS[2], use_container_width=True)
    st.sidebar.image(LOGOS[3], use_container_width=True)