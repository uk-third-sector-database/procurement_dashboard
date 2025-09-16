""" Home page for the procurement dashboard app. """
from pathlib import Path

import duckdb
import sidebar
import streamlit as st

SELECT_ALL = "<ALL>"

TEXT_MAPPING = {
    "DESC": "largest",
    "ASC": "lowest",
}

NULLS = "NULLS LAST"


def quote_ident(name: str) -> str:
    """
    Safely quote an identifier (column/table/view name) for SQL in DuckDB.
    Doubles internal quotes to prevent injection/SQL errors.
    """
    return '"' + name.replace('"', '""') + '"'


st.set_page_config(
    layout="wide",
    page_title="Procurement Dashboard",
    page_icon=":receipt:",
    initial_sidebar_state="expanded",
)

sidebar.display()

# configure the relation to the parquet data file
# -----------------------------------------------
FILEPATH = Path(__file__).parent.parent.parent / "data" / "processed" / "dataset.parquet"
# establish a connection to DuckDB
con = duckdb.connect()
# open a relation with the parquet file
rel = con.read_parquet(str(FILEPATH))
rel.create_view("data", replace=True)

# build the sources filter in the sidebar
COLUMN_NAME = "Source"
sources = (
    con.execute(f"SELECT DISTINCT {COLUMN_NAME} FROM data ORDER BY 1")
    .fetchdf()[COLUMN_NAME]
    .tolist()
)

selected_sources = st.sidebar.multiselect(
    COLUMN_NAME,
    options=sources,
    default=sources,
    help="Select multiple sources to filter the dataset.",
)

# build the sidebar display settings
with st.sidebar.expander("Display settings", expanded=True):
    sort_by = st.selectbox(
        "Sort by",
        options=["Total value payments", "Total payments"],
        index=0,
        help="Select the column to sort by.",
    )

    n_displayed_records = st.number_input(
        "Records to display",
        min_value=10,
        max_value=1000,
        value=500,
        step=10,
        help="Select the number of records to display.",
    )

    order = st.radio(
        "Order",
        options=["DESC", "ASC"],
        index=0,
        horizontal=True,
        help="Select the order to sort by.",
    )


if not selected_sources:
    st.warning("Please select at least one source to display any data.")
    st.stop()

WHERE_CLAUSE = f"{quote_ident(COLUMN_NAME)} IN ({', '.join('?' for _ in selected_sources)})"

# get stats for the filtered dataset
n_records = con.execute(
    f"SELECT COUNT(*) FROM data WHERE {WHERE_CLAUSE}", selected_sources
).fetchone()[0]

# get the dataset to display
dset = con.execute(
    f"""
    SELECT *
    FROM data
    WHERE {WHERE_CLAUSE}
    ORDER BY {quote_ident(sort_by)} {order} {NULLS}
    LIMIT ?
    """,
    selected_sources + [n_displayed_records],
).fetchdf()

st.metric("Selected records", f"{n_records:,}")

st.write(f"""
{n_displayed_records} records with the **{TEXT_MAPPING[order]}** values for **{sort_by}**.
""")

st.dataframe(dset, use_container_width=True, hide_index=True)
