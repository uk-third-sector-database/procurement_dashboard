"""Home page for the procurement dashboard app."""

from pathlib import Path

import duckdb
import pandas as pd
import sidebar
import streamlit as st


def quote_ident(name: str) -> str:
    """
    Safely quote an identifier (column/table/view name) for SQL in DuckDB.
    Doubles internal quotes to prevent injection/SQL errors.
    """
    return '"' + name.replace('"', '""') + '"'


TEXT_EITHER = "Do not apply filter"

TEXT_MAPPING = {
    "DESC": "largest",
    "ASC": "lowest",
}

NULLS = "NULLS LAST"
COLUMNS_TO_DISPLAY = [
    "Source",
    "Department",
    "Amount",
    "Supplier",
    "Payment date",
    "Latitude",
    "Longitude",
    "Total value payments",
    "Total payments",
    "Is spine?",
    "Manual match to spine?",
    "Other match to spine?",
    "Removed?",
    "Removal date",
]
COLUMNS_TO_DISPLAY_SQL = ", ".join(quote_ident(c) for c in COLUMNS_TO_DISPLAY)

COLUMN_TO_DISPLAY_STYLES = {
    "Amount": "{:,.0f}",
    "Total value payments": "{:,.0f}",
    "Total payments": "{:,.0f}",
}

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

# get the data columns
# column_names = (
#     con.execute("SELECT name FROM pragma_table_info('data')")
#     .fetchdf()["name"]
#     .tolist()
# )
# print(column_names)

# build the sidebar display settings
with st.sidebar.expander("Display settings", expanded=False):
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


# get data from the file to build various widgets
COLUMN_SOURCE = "Source"
sources = (
    con.execute(
        f"""
        SELECT DISTINCT {COLUMN_SOURCE} FROM data ORDER BY 1
        """
    )
    .fetchdf()[COLUMN_SOURCE]
    .tolist()
)

COLUMN_LATITUDE = "Latitude"
latitudes = (
    con.execute(
        f"""
        SELECT DISTINCT {COLUMN_LATITUDE} FROM data ORDER BY 1
        """
    )
    .fetchdf()[COLUMN_LATITUDE]
    .tolist()
)

COLUMN_LONGITUDE = "Longitude"
longitudes = (
    con.execute(
        f"""
        SELECT DISTINCT {COLUMN_LONGITUDE} FROM data ORDER BY 1
        """
    )
    .fetchdf()[COLUMN_LONGITUDE]
    .tolist()
)

COLUMN_PAYMENT_DATE = "Payment date"
KEY_PAYMENT_DATE_RANGE = f"{COLUMN_PAYMENT_DATE}_range"
dmin, dmax = con.execute(
    f"""
    SELECT 
    MIN(CAST({quote_ident(COLUMN_PAYMENT_DATE)} AS DATE)),
    MAX(CAST({quote_ident(COLUMN_PAYMENT_DATE)} AS DATE))
    FROM data
    """
).fetchone()
if KEY_PAYMENT_DATE_RANGE not in st.session_state:
    # set the initial value to the full range
    st.session_state[KEY_PAYMENT_DATE_RANGE] = (dmin, dmax)

selected_sources = st.sidebar.multiselect(
    COLUMN_SOURCE,
    options=sources,
    default=sources,
    help="Select multiple sources to filter the dataset.",
)

COLUMN_SPINE = "Is spine?"
is_spine = st.sidebar.selectbox(
    COLUMN_SPINE,
    options=[None, True, False],
    format_func=lambda x: TEXT_EITHER if x is None else str(x),
    help=f"Choose value for the '{COLUMN_SPINE}' column.",
)

COLUMN_MANUAL_MATCH = "Manual match to spine?"
is_manual_match = st.sidebar.selectbox(
    COLUMN_MANUAL_MATCH,
    options=[None, True, False],
    format_func=lambda x: TEXT_EITHER if x is None else str(x),
    help=f"Choose value for the '{COLUMN_MANUAL_MATCH}' column.",
)

COLUMN_OTHER_MATCH = "Other match to spine?"
is_other_match = st.sidebar.selectbox(
    COLUMN_OTHER_MATCH,
    options=[None, True, False],
    format_func=lambda x: TEXT_EITHER if x is None else str(x),
    help=f"Choose value for the '{COLUMN_OTHER_MATCH}' column.",
)

COLUMN_REMOVED = "Removed?"
is_removed = st.sidebar.selectbox(
    COLUMN_REMOVED,
    options=[None, True, False],
    format_func=lambda x: TEXT_EITHER if x is None else str(x),
    help=f"Choose value for the '{COLUMN_REMOVED}' column.",
)

date_cols = st.sidebar.columns([7, 1])
# two lines to vertically align the button with the date input
date_cols[1].markdown(" ")
date_cols[1].markdown(" ")
if date_cols[1].button("↺", help="Reset date range"):
    st.session_state[KEY_PAYMENT_DATE_RANGE] = (dmin, dmax)
# value not given because it is set in the session state KEY_PAYMENT_DATE_RANGE
date_range = date_cols[0].date_input(
    COLUMN_PAYMENT_DATE,
    min_value=dmin,
    max_value=dmax,
    format="DD/MM/YYYY",
    help="Select the date range for the payment date.",
    key=KEY_PAYMENT_DATE_RANGE,
)

if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.sidebar.warning("Please select both a start and end date.")
    st.stop()
else:
    start_date, end_date = date_range
    if start_date > end_date:
        st.sidebar.warning("Please ensure the start date is before the end date.")
        st.stop()


if not selected_sources:
    st.warning("Please select at least one source to display any data.")
    st.stop()

# build the WHERE clause and parameters
clauses, params = [], []

# source
PLACEHOLDERS = ", ".join("?" for _ in selected_sources)
clauses.append(f"{quote_ident(COLUMN_SOURCE)} IN ({PLACEHOLDERS})")
params.extend(selected_sources)

# is spine
if is_spine is not None:
    clauses.append(f"{quote_ident(COLUMN_SPINE)} = ?")
    params.append(is_spine)

# is manual match
if is_manual_match is not None:
    clauses.append(f"{quote_ident(COLUMN_MANUAL_MATCH)} = ?")
    params.append(is_manual_match)

# is other match
if is_other_match is not None:
    clauses.append(f"{quote_ident(COLUMN_OTHER_MATCH)} = ?")
    params.append(is_other_match)

# removed
if is_removed is not None:
    clauses.append(f"{quote_ident(COLUMN_REMOVED)} = ?")
    params.append(is_removed)

# date range
clauses.append(f"CAST({quote_ident(COLUMN_PAYMENT_DATE)} AS DATE) BETWEEN ? AND ?")
params.extend(st.session_state[KEY_PAYMENT_DATE_RANGE])

WHERE_CLAUSE = " AND ".join(clauses) if clauses else "TRUE"

# get stats for the filtered dataset
n_records = con.execute(f"SELECT COUNT(*) FROM data WHERE {WHERE_CLAUSE}", params).fetchone()[0]

# get the dataset to display
dset = con.execute(
    f"""
    SELECT {COLUMNS_TO_DISPLAY_SQL}
    FROM data
    WHERE {WHERE_CLAUSE}
    ORDER BY {quote_ident(sort_by)} {order} {NULLS}
    LIMIT ?
    """,
    params + [n_displayed_records],
).fetchdf()

if dset.empty:
    st.warning("No records available for the selected filters.")
    st.stop()

st.metric("Selected records", f"{n_records:,}")

st.write(f"""
The **{n_displayed_records}** records with the **{TEXT_MAPPING[order]}** values for **{sort_by}**
""")

# format the columns to display
date_cols = ["Payment date", "Org seen - min date", "Org seen - max date"]
for col in date_cols:
    if col in dset.columns and pd.api.types.is_datetime64_any_dtype(dset[col]):
        dset[col] = dset[col].dt.strftime("%d/%m/%Y")
dset_styled = dset.style.format(COLUMN_TO_DISPLAY_STYLES)
st.dataframe(dset_styled, use_container_width=True, hide_index=True)
