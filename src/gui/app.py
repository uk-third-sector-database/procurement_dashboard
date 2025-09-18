"""Home page for the procurement dashboard app."""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import sidebar
import streamlit as st

import utils.columns as cols


def quote_ident(name: str) -> str:
    """
    Safely quote an identifier (column/table/view name) for SQL in DuckDB.
    Doubles internal quotes to prevent injection/SQL errors.
    """
    return '"' + name.replace('"', '""') + '"'


TEXT_EITHER = "Do not apply filter"

NULLS = "NULLS LAST"

COLUMNS_TO_DISPLAY = [
    cols.SOURCE,
    cols.DEPARTMENT,
    cols.AMOUNT,
    cols.SUPPLIER,
    cols.PAYMENT_DATE,
    cols.LATITUDE,
    cols.LONGITUDE,
    cols.SPINE,
    cols.MANUAL_MATCH,
    cols.OTHER_MATCH,
    cols.REMOVED,
    cols.REMOVAL_DATE,
]
COLUMNS_TO_DISPLAY_SQL = ", ".join(quote_ident(c) for c in COLUMNS_TO_DISPLAY)

COLUMNS_TO_DISPLAY_STYLES = {
    cols.AMOUNT: "{:,.0f}",
    cols.TOTAL_VALUE_PAYMENTS: "{:,.0f}",
    cols.TOTAL_PAYMENTS: "{:,.0f}",
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
    n_displayed_records = st.number_input(
        "Records to display",
        min_value=10,
        max_value=1000,
        value=500,
        step=10,
        help="Select the number of records to display.",
    )


# get data from the file to build various widgets
sources = (
    con.execute(
        f"""
        SELECT DISTINCT {cols.SOURCE} FROM data ORDER BY 1
        """
    )
    .fetchdf()[cols.SOURCE]
    .tolist()
)

latitudes = (
    con.execute(
        f"""
        SELECT DISTINCT {cols.LATITUDE} FROM data ORDER BY 1
        """
    )
    .fetchdf()[cols.LATITUDE]
    .tolist()
)

longitudes = (
    con.execute(
        f"""
        SELECT DISTINCT {cols.LONGITUDE} FROM data ORDER BY 1
        """
    )
    .fetchdf()[cols.LONGITUDE]
    .tolist()
)

KEY_PAYMENT_DATE_RANGE = f"{cols.PAYMENT_DATE}_range"
dmin, dmax = con.execute(
    f"""
    SELECT 
    MIN(CAST({quote_ident(cols.PAYMENT_DATE)} AS DATE)),
    MAX(CAST({quote_ident(cols.PAYMENT_DATE)} AS DATE))
    FROM data
    """
).fetchone()
if KEY_PAYMENT_DATE_RANGE not in st.session_state:
    # set the initial value to the full range
    st.session_state[KEY_PAYMENT_DATE_RANGE] = (dmin, dmax)

selected_sources = st.sidebar.multiselect(
    cols.SOURCE,
    options=sources,
    default=sources,
    help="Select multiple sources to filter the dataset.",
)


is_spine = st.sidebar.selectbox(
    cols.SPINE,
    options=[None, True, False],
    format_func=lambda x: TEXT_EITHER if x is None else str(x),
    help=f"Choose value for the '{cols.SPINE}' column.",
)

is_manual_match = st.sidebar.selectbox(
    cols.MANUAL_MATCH,
    options=[None, True, False],
    format_func=lambda x: TEXT_EITHER if x is None else str(x),
    help=f"Choose value for the '{cols.MANUAL_MATCH}' column.",
)

is_other_match = st.sidebar.selectbox(
    cols.OTHER_MATCH,
    options=[None, True, False],
    format_func=lambda x: TEXT_EITHER if x is None else str(x),
    help=f"Choose value for the '{cols.OTHER_MATCH}' column.",
)

is_removed = st.sidebar.selectbox(
    cols.REMOVED,
    options=[None, True, False],
    format_func=lambda x: TEXT_EITHER if x is None else str(x),
    help=f"Choose value for the '{cols.REMOVED}' column.",
)

date_cols = st.sidebar.columns([7, 1])
# two lines to vertically align the button with the date input
date_cols[1].markdown(" ")
date_cols[1].markdown(" ")
if date_cols[1].button("↺", help="Reset date range"):
    st.session_state[KEY_PAYMENT_DATE_RANGE] = (dmin, dmax)
# value not given because it is set in the session state KEY_PAYMENT_DATE_RANGE
date_range = date_cols[0].date_input(
    cols.PAYMENT_DATE,
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
clauses.append(f"{quote_ident(cols.SOURCE)} IN ({PLACEHOLDERS})")
params.extend(selected_sources)

# is spine
if is_spine is not None:
    clauses.append(f"{quote_ident(cols.SPINE)} = ?")
    params.append(is_spine)

# is manual match
if is_manual_match is not None:
    clauses.append(f"{quote_ident(cols.MANUAL_MATCH)} = ?")
    params.append(is_manual_match)

# is other match
if is_other_match is not None:
    clauses.append(f"{quote_ident(cols.OTHER_MATCH)} = ?")
    params.append(is_other_match)

# removed
if is_removed is not None:
    clauses.append(f"{quote_ident(cols.REMOVED)} = ?")
    params.append(is_removed)

# date range
clauses.append(f"CAST({quote_ident(cols.PAYMENT_DATE)} AS DATE) BETWEEN ? AND ?")
params.extend(st.session_state[KEY_PAYMENT_DATE_RANGE])

WHERE_CLAUSE = " AND ".join(clauses) if clauses else "TRUE"

# get stats for the filtered dataset
n_records = con.execute(f"SELECT COUNT(*) FROM data WHERE {WHERE_CLAUSE}", params).fetchone()[0]

n_suppliers = con.execute(
    f"SELECT COUNT(DISTINCT {quote_ident(cols.SUPPLIER)}) FROM data WHERE {WHERE_CLAUSE}", params
).fetchone()[0]

total_amount = con.execute(
    f"SELECT SUM({quote_ident(cols.AMOUNT)}) FROM data WHERE {WHERE_CLAUSE}", params
).fetchone()[0]

# get the raw dataset to display as top records by Amount
dset_raw = con.execute(
    f"""
    SELECT {COLUMNS_TO_DISPLAY_SQL}
    FROM data
    WHERE {WHERE_CLAUSE}
    ORDER BY {quote_ident(cols.AMOUNT)} DESC {NULLS}
    LIMIT ?
    """,
    params + [n_displayed_records],
).fetchdf()

if dset_raw.empty:
    st.warning("No records available for the selected filters.")
    st.stop()

cols_metrics = st.columns(3)
cols_metrics[0].metric("Transactions", f"{n_records:,}")
cols_metrics[1].metric("Suppliers", f"{n_suppliers:,}")
cols_metrics[2].metric("Total amount", f"{total_amount:,.0f}")

tabs_views = st.tabs(["Raw data", "Aggregates by supplier", "Timecourse"])

with tabs_views[0]:
    if n_records > n_displayed_records:
        # more records available than displayed, inform the user about the display selection made
        st.write(f"""
        The top **{n_displayed_records}** selected transactions by **{cols.AMOUNT}**
        """)

    # format the columns to display
    date_cols = ["Payment date", "Org seen - min date", "Org seen - max date"]
    for col in date_cols:
        if col in dset_raw.columns and pd.api.types.is_datetime64_any_dtype(dset_raw[col]):
            dset_raw[col] = dset_raw[col].dt.strftime("%d/%m/%Y")
    dset_styled = dset_raw.style.format(COLUMNS_TO_DISPLAY_STYLES)
    st.dataframe(dset_styled, use_container_width=True, hide_index=True)

with tabs_views[1]:
    tabs_suppliers = st.tabs(
        [f"Ranked by {cols.TOTAL_VALUE_PAYMENTS}", f"Ranked by {cols.TOTAL_PAYMENTS}"]
    )
    with tabs_suppliers[0]:
        dset_suppliers = con.execute(
            f"""
                WITH filtered AS (
                    SELECT {cols.SUPPLIER},
                            {cols.AMOUNT}
                FROM data
                WHERE {WHERE_CLAUSE}
                ),
                agg AS (
                    SELECT
                        {cols.SUPPLIER},
                        SUM({cols.AMOUNT}) AS {quote_ident(cols.TOTAL_VALUE_PAYMENTS)},
                        COUNT(*) AS {quote_ident(cols.TOTAL_PAYMENTS)}
                    FROM filtered
                    GROUP BY {cols.SUPPLIER}
                )
                SELECT *
                FROM agg
                ORDER BY {quote_ident(cols.TOTAL_VALUE_PAYMENTS)} DESC NULLS LAST
                LIMIT ?
            """,
            params + [int(n_displayed_records)],
        ).fetchdf()

        if dset_suppliers.shape[0] < n_suppliers:
            st.write(
                f"""
                    The top **{dset_suppliers.shape[0]}** suppliers by
                    **{cols.TOTAL_VALUE_PAYMENTS}**
                """
            )
        dset_styled = dset_suppliers.style.format(COLUMNS_TO_DISPLAY_STYLES)
        st.dataframe(dset_styled, use_container_width=True, hide_index=True)

    with tabs_suppliers[1]:
        dset_suppliers = con.execute(
            f"""
                WITH filtered AS (
                    SELECT {cols.SUPPLIER},
                           {cols.AMOUNT}
                FROM data
                WHERE {WHERE_CLAUSE}
                ),
                agg AS (
                    SELECT
                        {cols.SUPPLIER},
                        SUM({cols.AMOUNT}) AS {quote_ident(cols.TOTAL_VALUE_PAYMENTS)},
                        COUNT(*) AS {quote_ident(cols.TOTAL_PAYMENTS)}
                    FROM filtered
                    GROUP BY {cols.SUPPLIER}
                )
                SELECT *
                FROM agg
                ORDER BY {quote_ident(cols.TOTAL_PAYMENTS)} DESC NULLS LAST
                LIMIT ?
            """,
            params + [int(n_displayed_records)],
        ).fetchdf()

        if dset_suppliers.shape[0] < n_suppliers:
            st.write(
                f"""
                    The top **{dset_suppliers.shape[0]}** suppliers by
                    **{cols.TOTAL_PAYMENTS}**
                """
            )
        dset_styled = dset_suppliers.style.format(COLUMNS_TO_DISPLAY_STYLES)
        st.dataframe(dset_styled, use_container_width=True, hide_index=True)
with tabs_views[2]:
    COLUMN_DATE = "Date"
    COLUMN_TRANSACTIONS = "Transactions"
    COLUMN_VALUE = "Total amount"
    dset_tcourse_transactions = con.execute(
        f"""
        SELECT
            strftime({quote_ident(cols.PAYMENT_DATE)}, '%Y-%m') AS {quote_ident(COLUMN_DATE)},
            COUNT(*) AS {quote_ident(COLUMN_TRANSACTIONS)},
            SUM({quote_ident(cols.AMOUNT)}) AS {quote_ident(COLUMN_VALUE)}
        FROM data
        WHERE {WHERE_CLAUSE}
        GROUP BY {quote_ident(COLUMN_DATE)}
        ORDER BY {quote_ident(COLUMN_DATE)}
        """,
        params,
    ).fetchdf()

    dset_tcourse_transactions[COLUMN_DATE] = pd.to_datetime(dset_tcourse_transactions[COLUMN_DATE])

    column_to_plot = st.radio(
        "Choose what to plot", options=[COLUMN_TRANSACTIONS, COLUMN_VALUE], index=0, horizontal=True
    )

    fig = px.bar(
        dset_tcourse_transactions,
        x=COLUMN_DATE,
        y=column_to_plot,
        labels={COLUMN_DATE: ""},
        title="",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    fig.update_yaxes(tickformat=",")
    fig.update_xaxes(dtick="M12", tickformat="%b %Y", ticklabelmode="period")

    st.plotly_chart(fig, use_container_width=True)
