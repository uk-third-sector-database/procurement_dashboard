"""Home page for the procurement dashboard app."""

from types import SimpleNamespace

import duckdb
import geopandas as gpd
import pandas as pd
import plotly.express as px
import sidebar as sd
import streamlit as st

import utils.shared as shared
import gui.utils as utils 
from utils.columns import (
    COLS,
    COLS_SQL,
    COLUMNS_DATE,
    COLUMNS_TO_DISPLAY_SQL,
    COLUMNS_TO_DISPLAY_STYLES,
    quote_ident,
)

cols = SimpleNamespace(**COLS)
cols_sql = SimpleNamespace(**COLS_SQL)

TEXT_EITHER = "Do not apply filter"

NULLS = "NULLS LAST"

st.set_page_config(
    layout="wide",
    page_title="Procurement Dashboard",
    page_icon=":receipt:",
    initial_sidebar_state="expanded",
)

sd.display()

# configure the relation to the parquet data file
# -----------------------------------------------
# establish a connection to DuckDB and open a relation with the parquet file
con = duckdb.connect()
rel = con.read_parquet(str(shared.FILEPATH))
rel.create_view("data", replace=True)

# get the data columns
# column_names = (
#     con.execute("SELECT name FROM pragma_table_info('data')")
#     .fetchdf()["name"]
#     .tolist()
# )
# print(column_names)

# build the sidebar display settings
n_displayed_records = st.sidebar.number_input(
    "Maximum number of records to display", min_value=10, max_value=500, value=250, step=10
)


# get data from the file to build various widgets
sources = (
    con.execute(
        f"""
        SELECT DISTINCT {cols_sql.SOURCE} FROM data ORDER BY 1
        """
    )
    .fetchdf()[cols.SOURCE]
    .tolist()
)


KEY_PAYMENT_DATE_RANGE = f"{cols.PAYMENT_DATE}_range"
dmin, dmax = con.execute(
    f"""
    SELECT 
    MIN(CAST({cols_sql.PAYMENT_DATE} AS DATE)),
    MAX(CAST({cols_sql.PAYMENT_DATE} AS DATE))
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

if is_spine is True:
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

    nuts_name_1s = (
        con.execute(
            f"""
            SELECT DISTINCT {cols_sql.NUTS_NAME_1} FROM data ORDER BY 1
            """
        )
        .fetchdf()[cols.NUTS_NAME_1]
        .tolist()
    )
    nuts_name_1s = utils.process_nuts_names(nuts_name_1s)

    selected_nuts_1s = st.sidebar.multiselect(
        "NUTS Level 1 region", options=nuts_name_1s, default=nuts_name_1s
    )
    if selected_nuts_1s:
        nuts_name_2s = (
            con.execute(
                f"""
                SELECT DISTINCT {cols_sql.NUTS_NAME_2}
                FROM data
                WHERE {cols_sql.NUTS_NAME_1} IN ({", ".join(["?"] * len(selected_nuts_1s))})
                ORDER BY 1
                """,
                selected_nuts_1s,  # params for the IN clause
            )
            .fetchdf()[cols.NUTS_NAME_2]
            .tolist()
        )
        nuts_name_2s = utils.process_nuts_names(nuts_name_2s)

        selected_nuts_2s = st.sidebar.multiselect(
            "NUTS Level 2 region", options=nuts_name_2s, default=nuts_name_2s, key="nuts_name_2s"
        )
        if selected_nuts_2s:
            nuts_name_3s = (
                con.execute(
                    f"""
                    SELECT DISTINCT {cols_sql.NUTS_NAME_3}
                    FROM data
                    WHERE {cols_sql.NUTS_NAME_2} IN ({", ".join(["?"] * len(selected_nuts_2s))})
                    ORDER BY 1
                    """,
                    selected_nuts_2s,  # params for the IN clause
                )
                .fetchdf()[cols.NUTS_NAME_3]
                .tolist()
            )

            nuts_name_3s = utils.process_nuts_names(nuts_name_3s)

            selected_nuts_3s = st.sidebar.multiselect(
                "NUTS Level 3 region",
                options=nuts_name_3s,
                default=nuts_name_3s,
                key="nuts_name_3s",
            )
else:
    selected_nuts_1s = None
    selected_nuts_2s = None
    is_manual_match = None
    is_other_match = None

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
clauses.append(f"{cols_sql.SOURCE} IN ({PLACEHOLDERS})")
params.extend(selected_sources)

# nuts_name_1s
if selected_nuts_1s:
    PLACEHOLDERS = ", ".join("?" for _ in selected_nuts_1s)
    clauses.append(f"{cols_sql.NUTS_NAME_1} IN ({PLACEHOLDERS})")
    params.extend(selected_nuts_1s)

# is spine
if is_spine is not None:
    clauses.append(f"{cols_sql.SPINE} = ?")
    params.append(is_spine)

# is manual match
if is_manual_match is not None:
    clauses.append(f"{cols_sql.MANUAL_MATCH} = ?")
    params.append(is_manual_match)

# is other match
if is_other_match is not None:
    clauses.append(f"{cols_sql.OTHER_MATCH} = ?")
    params.append(is_other_match)

# removed
if is_removed is not None:
    clauses.append(f"{cols_sql.REMOVED} = ?")
    params.append(is_removed)

# date range
clauses.append(f"CAST({cols_sql.PAYMENT_DATE} AS DATE) BETWEEN ? AND ?")
params.extend(st.session_state[KEY_PAYMENT_DATE_RANGE])

WHERE_CLAUSE = " AND ".join(clauses) if clauses else "TRUE"

# get stats for the filtered dataset
n_transactions = con.execute(f"SELECT COUNT(*) FROM data WHERE {WHERE_CLAUSE}", params).fetchone()[
    0
]

n_suppliers = con.execute(
    f"SELECT COUNT(DISTINCT {cols_sql.SUPPLIER}) FROM data WHERE {WHERE_CLAUSE}", params
).fetchone()[0]

total_amount = con.execute(
    f"SELECT SUM({cols_sql.AMOUNT}) FROM data WHERE {WHERE_CLAUSE}", params
).fetchone()[0]

if is_spine is None and n_transactions > 0:
    WHERE_CLAUSE_SPINE = WHERE_CLAUSE + f" AND {cols_sql.SPINE} = TRUE"
    n_suppliers_spine = con.execute(
        f"SELECT COUNT(DISTINCT {cols_sql.SUPPLIER}) FROM data WHERE {WHERE_CLAUSE_SPINE}",
        params,
    ).fetchone()[0]
    n_transactions_spine = con.execute(
        f"SELECT COUNT(*) FROM data WHERE {WHERE_CLAUSE_SPINE}", params
    ).fetchone()[0]
    total_amount_spine = con.execute(
        f"SELECT SUM({cols_sql.AMOUNT}) FROM data WHERE {WHERE_CLAUSE_SPINE}", params
    ).fetchone()[0]
else:
    n_suppliers_spine = None
    n_transactions_spine = None
    total_amount_spine = None


# get the raw dataset to display as top records by Amount
dset_raw = con.execute(
    f"""
    SELECT {COLUMNS_TO_DISPLAY_SQL}
    FROM data
    WHERE {WHERE_CLAUSE}
    ORDER BY {cols_sql.AMOUNT} DESC {NULLS}
    LIMIT ?
    """,
    params + [n_displayed_records],
).fetchdf()

if dset_raw.empty:
    st.warning("No records available for the selected filters.")
    st.stop()

cols_metrics = st.columns(3)

with cols_metrics[0].container(border=True):
    if is_spine is not True and n_suppliers_spine is not None:
        st.metric("🏢 Suppliers - all", f"{n_suppliers:,}")
        st.metric("Suppliers - spine (TSO)", f"{n_suppliers_spine:,}")
    else:
        st.metric("🏢 Suppliers", f"{n_suppliers:,}")
with cols_metrics[1].container(border=True):
    if is_spine is not True and n_transactions_spine is not None:
        st.metric("🤝 Transactions - all", f"{n_transactions:,}")
        st.metric("Transactions - spine (TSO)", f"{n_transactions_spine:,}")
    else:
        st.metric("🤝 Transactions", f"{n_transactions:,}")
with cols_metrics[2].container(border=True):
    if is_spine is not True and total_amount_spine is not None:
        st.metric("💷 Total amount - all", f"{total_amount:,.0f}")
        st.metric("Total amount - spine (TSO)", f"{total_amount_spine:,.0f}")
    else:
        st.metric("💷 Total amount", f"{total_amount:,.0f}")

tabs_views = st.tabs(
    ["Raw data", "Aggregates by supplier", "Timecourse", "Geographical distribution"]
)

with tabs_views[0]:
    if n_transactions > n_displayed_records:
        # more records available than displayed, inform the user about the display selection made
        st.write(f"""
        The top **{n_displayed_records}** selected transactions by **{cols.AMOUNT}**
        """)

    # format the columns to display
    for col in COLUMNS_DATE:
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
                    SELECT {cols_sql.SUPPLIER},
                            {cols_sql.AMOUNT}
                FROM data
                WHERE {WHERE_CLAUSE}
                ),
                agg AS (
                    SELECT
                        {cols_sql.SUPPLIER},
                        SUM({cols_sql.AMOUNT}) AS {cols_sql.TOTAL_VALUE_PAYMENTS},
                        COUNT(*) AS {cols_sql.TOTAL_PAYMENTS}
                    FROM filtered
                    GROUP BY {cols_sql.SUPPLIER}
                )
                SELECT *
                FROM agg
                ORDER BY {cols_sql.TOTAL_VALUE_PAYMENTS} DESC NULLS LAST
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
                    SELECT {cols_sql.SUPPLIER},
                           {cols_sql.AMOUNT}
                FROM data
                WHERE {WHERE_CLAUSE}
                ),
                agg AS (
                    SELECT
                        {cols_sql.SUPPLIER},
                        SUM({cols_sql.AMOUNT}) AS {cols_sql.TOTAL_VALUE_PAYMENTS},
                        COUNT(*) AS {cols_sql.TOTAL_PAYMENTS}
                    FROM filtered
                    GROUP BY {cols_sql.SUPPLIER}
                )
                SELECT *
                FROM agg
                ORDER BY {cols_sql.TOTAL_PAYMENTS} DESC NULLS LAST
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
    COLUMN_DATE = cols.DATE
    COLUMN_TRANSACTIONS = cols.PAYMENTS
    COLUMN_VALUE = cols.VALUE
    dset_tcourse_transactions = con.execute(
        f"""
        SELECT
            strftime({cols_sql.PAYMENT_DATE}, '%Y-%m') AS {quote_ident(COLUMN_DATE)},
            COUNT(*) AS {quote_ident(COLUMN_TRANSACTIONS)},
            SUM({cols_sql.AMOUNT}) AS {quote_ident(COLUMN_VALUE)}
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

with tabs_views[3]:
    if is_spine is not True:
        st.info(
            f"""
            Geographical distribution is only available when filtering for
            '{cols.SPINE}' = True.
            """
        )
        st.stop()

    nuts = gpd.read_file(shared.SHAPE_FILE).to_crs(epsg=4326)
    nuts = nuts[(nuts.CNTR_CODE == "UK") & (nuts.NUTS_ID != "UKN")].copy()

    cols_maps_selections = st.columns(2)
    with cols_maps_selections[0]:
        nuts_level = st.selectbox("NUTS level to display", options=[1, 2, 3], index=0)
    with cols_maps_selections[1]:
        column_to_plot = st.radio(
            "Choose what to plot on the map",
            options=[cols.TOTAL_PAYMENTS, cols.TOTAL_VALUE_PAYMENTS],
            index=0,
            horizontal=True,
        )
    nuts_display = nuts[nuts.LEVL_CODE == nuts_level]

    COLUMN_NUTS_ID = f"NUTS ID {nuts_level}"
    dset_nuts = con.execute(
        f"""
            WITH filtered AS (
                SELECT {quote_ident(COLUMN_NUTS_ID)},
                        {cols_sql.AMOUNT}
            FROM data
            WHERE {WHERE_CLAUSE}
            ),
            agg AS (
                SELECT
                    {quote_ident(COLUMN_NUTS_ID)},
                    SUM({cols_sql.AMOUNT}) AS {cols_sql.TOTAL_VALUE_PAYMENTS},
                    COUNT(*) AS {cols_sql.TOTAL_PAYMENTS}
                FROM filtered
                WHERE {quote_ident(COLUMN_NUTS_ID)} IS NOT NULL
                GROUP BY {quote_ident(COLUMN_NUTS_ID)}
            )
            SELECT *
            FROM agg
        """,
        params,
    ).fetchdf()

    # merge nuts_display with dset_nuts on NUTS_ID_1
    nuts_display = nuts_display.merge(
        dset_nuts, how="left", left_on="NUTS_ID", right_on=COLUMN_NUTS_ID
    )
    nuts_display[cols.TOTAL_VALUE_PAYMENTS] = nuts_display[cols.TOTAL_VALUE_PAYMENTS].fillna(0)
    nuts_display[cols.TOTAL_PAYMENTS] = nuts_display[cols.TOTAL_PAYMENTS].fillna(0)
    nuts_display.set_index("NUTS_ID", inplace=True)
    fig = px.choropleth(
        nuts_display,
        geojson=nuts_display.geometry,
        locations=nuts_display.index,
        hover_name="NUTS_NAME",
        color=column_to_plot,
        color_continuous_scale="Blues",
        projection="mercator",
    )
    fig.update_geos(fitbounds="locations", visible=False)

    cols_maps = st.columns(2)
    with cols_maps[0]:
        st.dataframe(
            nuts_display[["NUTS_NAME", cols.TOTAL_PAYMENTS, cols.TOTAL_VALUE_PAYMENTS]],
            use_container_width=False,
            hide_index=False,
        )
    with cols_maps[1]:
        st.plotly_chart(fig, use_container_width=True)
