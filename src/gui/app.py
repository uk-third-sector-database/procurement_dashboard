"""Home page for the procurement dashboard app."""

from types import SimpleNamespace

import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st

import gui.db as db
import gui.sidebar as sd
import gui.utils as utils
import utilities.shared as shared
from gui.content import TEXT, WIDGETS
from utilities.columns import (
    COLS,
    COLS_SQL,
    COLUMNS_DATE,
    COLUMNS_TO_DISPLAY_SQL,
    COLUMNS_TO_DISPLAY_STYLES,
    REGISTRIES,
    quote_ident,
)

cols = SimpleNamespace(**COLS)
cols_sql = SimpleNamespace(**COLS_SQL)
text = SimpleNamespace(**TEXT)
widgets = SimpleNamespace(**WIDGETS)


NULLS = "NULLS LAST"

KEY_NUTS_NAME_SELECTION_1 = "multiselect_nuts_name_1"
KEY_NUTS_NAME_SELECTION_ALL_1 = "checkbox_select_all_nuts_1"
KEY_NUTS_NAME_SELECTION_2 = "multiselect_nuts_name_2"
KEY_NUTS_NAME_SELECTION_ALL_2 = "checkbox_select_all_nuts_2"
KEY_NUTS_NAME_SELECTION_3 = "multiselect_nuts_name_3"
KEY_NUTS_NAME_SELECTION_ALL_3 = "checkbox_select_all_nuts_3"

st.set_page_config(
    layout="wide",
    page_title=text.APP_TITLE,
    page_icon=":receipt:",
    initial_sidebar_state="expanded",
)

# display the sidebar top
sd.top()

# get the cached DuckDB connection with the data loaded as a view
con = db.get_con()

# sidebar widget to select the number of records to display
n_displayed_records = st.sidebar.number_input(**widgets.RECORDS_TO_DISPLAY)

# sidebar widget to select the sources to display
sources = db.fetch_distinct_values(con, cols.SOURCE)
selected_sources = st.sidebar.multiselect(cols.SOURCE, options=sources, default=sources)
if not selected_sources:
    st.sidebar.warning(text.ERROR_NO_SOURCE_SELECTED)
    st.stop()

# sidebar widget to select the payment date range with reset button
dmin, dmax = db.fetch_date_range(con, cols_sql.PAYMENT_DATE)
KEY_PAYMENT_DATE_RANGE = f"{cols.PAYMENT_DATE}_range"
if KEY_PAYMENT_DATE_RANGE not in st.session_state:
    st.session_state[KEY_PAYMENT_DATE_RANGE] = (dmin, dmax)

date_cols = st.sidebar.columns([7, 1], vertical_alignment="bottom")
with date_cols[1]:
    if st.button(**widgets.DATE_RANGE_RESET):
        st.session_state[KEY_PAYMENT_DATE_RANGE] = (dmin, dmax)
with date_cols[0]:
    date_range = date_cols[0].date_input(
        cols.PAYMENT_DATE,
        min_value=dmin,
        max_value=dmax,
        key=KEY_PAYMENT_DATE_RANGE,
        **widgets.DATE_RANGE,
    )

if not (isinstance(date_range, tuple | list) and len(date_range) == 2):
    st.sidebar.warning(text.ERROR_INCOMPLETE_DATE_RANGE)
    st.stop()
else:
    start_date, end_date = date_range
    if start_date > end_date:
        st.sidebar.warning(text.ERROR_INVALID_DATE_RANGE)
        st.stop()

# sidebar widget to filter for removed records
is_removed = st.sidebar.selectbox(
    cols.REMOVED,
    options=[None, True, False],
    format_func=lambda x: text.OPTION_NEITHER if x is None else str(x),
)

# sidebar widget to filter for spine records
is_spine = st.sidebar.selectbox(
    cols.SPINE,
    options=[None, True, False],
    format_func=lambda x: text.OPTION_NEITHER if x is None else str(x),
)

if is_spine is True:
    selected_nuts_1_ids = []
    selected_nuts_2_ids = []
    selected_nuts_3_ids = []

    nuts_level1, nuts_name_1s = db.fetch_nuts_level(con, level=1, where=None, params=[])

    if KEY_NUTS_NAME_SELECTION_1 not in st.session_state:
        st.session_state[KEY_NUTS_NAME_SELECTION_1] = []
    if KEY_NUTS_NAME_SELECTION_ALL_1 not in st.session_state:
        st.session_state[KEY_NUTS_NAME_SELECTION_ALL_1] = False

    cols_nuts_1 = st.sidebar.columns([0.75, 0.25], gap=None, vertical_alignment="center")
    cols_nuts_1[0].text("NUTS Level 1")
    with cols_nuts_1[1]:
        select_all_nuts_names_1 = st.checkbox("All", key=KEY_NUTS_NAME_SELECTION_ALL_1)
    if select_all_nuts_names_1 and st.session_state[KEY_NUTS_NAME_SELECTION_1] != nuts_name_1s:
        st.session_state[KEY_NUTS_NAME_SELECTION_1] = nuts_name_1s
        st.rerun()

    selected_nuts_1_names = st.sidebar.multiselect(
        "NUTS Level 1",
        options=nuts_name_1s,
        key=KEY_NUTS_NAME_SELECTION_1,
        label_visibility="collapsed",
        disabled=select_all_nuts_names_1,
    )
    if selected_nuts_1_names:
        selected_nuts_1_ids = nuts_level1.loc[
            nuts_level1[cols.NUTS_NAME_1].isin(selected_nuts_1_names), cols.NUTS_ID_1
        ].tolist()

        PLACEHOLDERS = ", ".join("?" for _ in selected_nuts_1_names)
        WHERE_CLAUSE = f"{quote_ident(COLS['NUTS_NAME_1'])} IN ({PLACEHOLDERS})"
        nuts_level2, nuts_name_2s = db.fetch_nuts_level(
            con=con,
            level=2,
            where=WHERE_CLAUSE,
            params=selected_nuts_1_names,
            order_by="NUTS_NAME_2",
        )

        if KEY_NUTS_NAME_SELECTION_2 not in st.session_state:
            st.session_state[KEY_NUTS_NAME_SELECTION_2] = []
        if KEY_NUTS_NAME_SELECTION_ALL_2 not in st.session_state:
            st.session_state[KEY_NUTS_NAME_SELECTION_ALL_2] = False

        cols_nuts_2 = st.sidebar.columns([0.75, 0.25], gap=None, vertical_alignment="center")
        cols_nuts_2[0].text("NUTS Level 2")
        with cols_nuts_2[1]:
            select_all_nuts_names_2 = st.checkbox("All", key=KEY_NUTS_NAME_SELECTION_ALL_2)
        if select_all_nuts_names_2 and st.session_state[KEY_NUTS_NAME_SELECTION_2] != nuts_name_2s:
            st.session_state[KEY_NUTS_NAME_SELECTION_2] = nuts_name_2s
            st.rerun()

        selected_nuts_2_names = st.sidebar.multiselect(
            "NUTS Level 2",
            options=nuts_name_2s,
            key=KEY_NUTS_NAME_SELECTION_2,
            label_visibility="collapsed",
            disabled=select_all_nuts_names_2,
        )

        if selected_nuts_2_names:
            selected_nuts_2_ids = nuts_level2.loc[
                nuts_level2[cols.NUTS_NAME_2].isin(selected_nuts_2_names), cols.NUTS_ID_2
            ].tolist()

            PLACEHOLDERS = ", ".join("?" for _ in selected_nuts_2_names)
            WHERE_CLAUSE = f"{quote_ident(COLS['NUTS_NAME_2'])} IN ({PLACEHOLDERS})"
            nuts_level3, nuts_name_3s = db.fetch_nuts_level(
                con=con,
                level=3,
                where=WHERE_CLAUSE,
                params=selected_nuts_2_names,
                order_by="NUTS_NAME_3",
            )

            if KEY_NUTS_NAME_SELECTION_3 not in st.session_state:
                st.session_state[KEY_NUTS_NAME_SELECTION_3] = []
            if KEY_NUTS_NAME_SELECTION_ALL_3 not in st.session_state:
                st.session_state[KEY_NUTS_NAME_SELECTION_ALL_3] = False

            cols_nuts_3 = st.sidebar.columns([0.75, 0.25], gap=None, vertical_alignment="center")
            cols_nuts_3[0].text("NUTS Level 3")
            with cols_nuts_3[1]:
                select_all_nuts_names_3 = st.checkbox("All", key=KEY_NUTS_NAME_SELECTION_ALL_3)
            if (
                select_all_nuts_names_3
                and st.session_state[KEY_NUTS_NAME_SELECTION_3] != nuts_name_3s
            ):
                st.session_state[KEY_NUTS_NAME_SELECTION_3] = nuts_name_3s
                st.rerun()

            selected_nuts_3_names = st.sidebar.multiselect(
                "NUTS Level 3",
                options=nuts_name_3s,
                key=KEY_NUTS_NAME_SELECTION_3,
                label_visibility="collapsed",
                disabled=select_all_nuts_names_3,
            )

            if len(selected_nuts_3_names):
                selected_nuts_3_ids = nuts_level3.loc[
                    nuts_level3[cols.NUTS_NAME_3].isin(selected_nuts_3_names), cols.NUTS_ID_3
                ].tolist()
    is_manual_match = st.sidebar.selectbox(
        cols.MANUAL_MATCH,
        options=[None, True, False],
        format_func=lambda x: text.OPTION_NEITHER if x is None else str(x),
        help=f"Choose value for the '{cols.MANUAL_MATCH}' column.",
    )

    is_other_match = st.sidebar.selectbox(
        cols.OTHER_MATCH,
        options=[None, True, False],
        format_func=lambda x: text.OPTION_NEITHER if x is None else str(x),
        help=f"Choose value for the '{cols.OTHER_MATCH}' column.",
    )
else:
    selected_nuts_1_names: list | None = None
    selected_nuts_1_ids: list | None = None
    selected_nuts_2_names: list | None = None
    selected_nuts_2_ids: list | None = None
    selected_nuts_3_names: list | None = None
    selected_nuts_3_ids: list | None = None
    is_manual_match: bool | None = None
    is_other_match: bool | None = None
    try:
        del st.session_state[KEY_NUTS_NAME_SELECTION_1]
        del st.session_state[KEY_NUTS_NAME_SELECTION_ALL_1]
        del st.session_state[KEY_NUTS_NAME_SELECTION_2]
        del st.session_state[KEY_NUTS_NAME_SELECTION_ALL_2]
        del st.session_state[KEY_NUTS_NAME_SELECTION_3]
        del st.session_state[KEY_NUTS_NAME_SELECTION_ALL_3]
    except KeyError:
        pass


# build the WHERE clause and parameters
clauses, params = [], []

# source
PLACEHOLDERS = ", ".join("?" for _ in selected_sources)
clauses.append(f"{cols_sql.SOURCE} IN ({PLACEHOLDERS})")
params.extend(selected_sources)

# nuts_name_1s
if selected_nuts_1_names and len(selected_nuts_1_names) > 0:
    PLACEHOLDERS = ", ".join("?" for _ in selected_nuts_1_names)
    clauses.append(f"{cols_sql.NUTS_NAME_1} IN ({PLACEHOLDERS})")
    params.extend(selected_nuts_1_names)

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

# transactions
row = con.execute(
    f"SELECT COUNT(*) FROM data WHERE {WHERE_CLAUSE}",
    params,
).fetchone()
assert row is not None, "COUNT(*) query returned no row"
n_transactions = row[0]

# suppliers
row = con.execute(
    f"SELECT COUNT(DISTINCT {cols_sql.SUPPLIER}) FROM data WHERE {WHERE_CLAUSE}",
    params,
).fetchone()
assert row is not None, "COUNT(DISTINCT Supplier) query returned no row"
n_suppliers = row[0]

# total amount
row = con.execute(
    f"SELECT SUM({cols_sql.AMOUNT}) FROM data WHERE {WHERE_CLAUSE}",
    params,
).fetchone()
assert row is not None, "SUM(Amount) query returned no row"
total_amount = row[0]

if is_spine is None and n_transactions > 0:
    WHERE_CLAUSE_SPINE = WHERE_CLAUSE + f" AND {cols_sql.SPINE} = TRUE"

    # suppliers (spine)
    row = con.execute(
        f"SELECT COUNT(DISTINCT {cols_sql.SUPPLIER}) FROM data WHERE {WHERE_CLAUSE_SPINE}",
        params,
    ).fetchone()
    assert row is not None, "COUNT(DISTINCT Supplier) query (spine) returned no row"
    n_suppliers_spine = row[0]

    # transactions (spine)
    row = con.execute(
        f"SELECT COUNT(*) FROM data WHERE {WHERE_CLAUSE_SPINE}",
        params,
    ).fetchone()
    assert row is not None, "COUNT(*) query (spine) returned no row"
    n_transactions_spine = row[0]

    # total amount (spine)
    row = con.execute(
        f"SELECT SUM({cols_sql.AMOUNT}) FROM data WHERE {WHERE_CLAUSE_SPINE}",
        params,
    ).fetchone()
    assert row is not None, "SUM(Amount) query (spine) returned no row"
    total_amount_spine = row[0]
else:
    n_suppliers_spine: int | None = None
    n_transactions_spine: int | None = None
    total_amount_spine: float | None = None


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
        st.metric("🏬 Suppliers - all", f"{n_suppliers:,}")
        st.metric("Suppliers - spine (TSO)", f"{n_suppliers_spine:,}")
    else:
        st.metric("🏬 Suppliers", f"{n_suppliers:,}")
with cols_metrics[1].container(border=True):
    if is_spine is not True and n_transactions_spine is not None:
        st.metric("🤝 Transactions - all", f"{n_transactions:,}")
        st.metric("Transactions - spine (TSO)", f"{n_transactions_spine:,}")
    else:
        st.metric("🤝 Transactions", f"{n_transactions:,}")
with cols_metrics[2].container(border=True):
    if is_spine is not True and total_amount_spine is not None:
        st.metric("💷 Value - all", f"{total_amount:,.0f}")
        st.metric("Value - spine (TSO)", f"{total_amount_spine:,.0f}")
    else:
        st.metric("💷 Value", f"{total_amount:,.0f}")

tabs_views = st.tabs(
    [
        "Raw data",
        "Supplier distributions",
        "Timecourses",
        "Geographical distributions",
        "Registry distributions",
    ]
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
        "Choose what to plot",
        options=[COLUMN_TRANSACTIONS, COLUMN_VALUE],
        index=0,
        horizontal=True,
        key="radio_column_to_plot_timecourse",
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
    if not is_spine or not all(
        [selected_nuts_1_names, selected_nuts_1_ids, selected_nuts_2_ids, selected_nuts_3_ids]
    ):
        st.info(
            f"""
            Geographical distribution is only available when filtering for
            '{cols.SPINE}' = True and valid selections for all the NUTS levels.
            """
        )
    else:
        nuts = gpd.read_file(shared.SHAPE_FILE).to_crs(epsg=4326)
        # nuts = nuts[nuts.CNTR_CODE == "UK"].copy()

        # mask = (
        #     (nuts["LEVL_CODE"].eq(1) & nuts["NUTS_ID"].isin(selected_nuts_1_ids))
        #     | (nuts["LEVL_CODE"].eq(2) & nuts["NUTS_ID"].isin(selected_nuts_2_ids))
        #     | (nuts["LEVL_CODE"].eq(3) & nuts["NUTS_ID"].isin(selected_nuts_3_ids))
        # )
        ids_1 = selected_nuts_1_ids or []
        ids_2 = selected_nuts_2_ids or []
        ids_3 = selected_nuts_3_ids or []

        mask = (
            (nuts["LEVL_CODE"].eq(1) & nuts["NUTS_ID"].isin(ids_1))
            | (nuts["LEVL_CODE"].eq(2) & nuts["NUTS_ID"].isin(ids_2))
            | (nuts["LEVL_CODE"].eq(3) & nuts["NUTS_ID"].isin(ids_3))
        )

        nuts = nuts[mask].copy()

        NUTS_LEVEL = 3
        nuts_display = nuts.loc[nuts.LEVL_CODE == NUTS_LEVEL]

        COLUMN_NUTS_ID = f"NUTS ID {NUTS_LEVEL}"
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

        col_sels = st.columns(2)
        with col_sels[0]:
            column_to_plot = st.radio(
                "Choose what to plot on the map",
                options=[cols.TOTAL_PAYMENTS, cols.TOTAL_VALUE_PAYMENTS],
                index=0,
                horizontal=True,
                key="radio_column_to_plot_choropleth",
            )
        with col_sels[1]:
            with st.popover("View legend", width="stretch"):
                st.text("")
                st.dataframe(
                    nuts_display[["NUTS_NAME"]],
                    use_container_width=True,
                    hide_index=False,
                )
        cols_maps = st.columns(2)
        with cols_maps[0]:
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

            fig.update_layout(
                margin=dict(l=0, r=0, t=20, b=0),
            )

            fig.update_layout(
                coloraxis_colorbar=dict(
                    orientation="h", x=0.5, xanchor="center", y=1.05, yanchor="bottom"
                )
            )

            st.plotly_chart(fig, use_container_width=True)
        with cols_maps[1]:
            st.dataframe(
                nuts_display[[cols.TOTAL_PAYMENTS, cols.TOTAL_VALUE_PAYMENTS]],
                use_container_width=True,
                hide_index=False,
            )
with tabs_views[4]:
    if is_spine is not True:
        st.info(
            f"""
            Registry distribution is only available when filtering for
            '{cols.SPINE}' = True.
            """
        )
        st.stop()
    else:
        dset_reg = pd.DataFrame()
        for registry in REGISTRIES:
            col_flag = quote_ident(registry)
            col_amount = cols_sql.AMOUNT

            dset_local = con.execute(
                f"""
                    SELECT
                        COUNT_IF({col_flag}) AS {cols_sql.TOTAL_PAYMENTS},
                        SUM(CASE WHEN {col_flag} THEN {col_amount} ELSE 0 END)
                            AS {cols_sql.TOTAL_VALUE_PAYMENTS}
                    FROM data
                    WHERE {WHERE_CLAUSE}
                """,
                params,
            ).fetchdf()
            dset_local.index = [registry]
            dset_reg = pd.concat([dset_reg, dset_local], axis=0)

        dset_reg.index.name = cols.REGISTRY
        dset_reg["Name"] = dset_reg.index.map(REGISTRIES)
        dset_reg = dset_reg[["Name", cols.TOTAL_PAYMENTS, cols.TOTAL_VALUE_PAYMENTS]]

        cols_selections = st.columns([0.2, 0.8])
        with cols_selections[0]:
            column_to_plot = st.radio(
                "Choose what to plot",
                options=[cols.TOTAL_PAYMENTS, cols.TOTAL_VALUE_PAYMENTS],
                index=0,
                horizontal=True,
                key="radio_column_to_plot_registry",
            )
        with cols_selections[1]:
            with st.popover("View registry aggregates data", width="stretch"):
                st.text("")
                st.dataframe(
                    dset_reg.reset_index().rename(columns={"Registry": "Code"}),
                    use_container_width=True,
                    hide_index=True,
                )

        cols_regs = st.columns(2)
        with cols_regs[0]:
            fig = px.bar(
                dset_reg.reset_index(),
                y=cols.REGISTRY,
                x=column_to_plot,
                title=column_to_plot,
                orientation="h",
                color=cols.REGISTRY,
                color_discrete_sequence=px.colors.qualitative.Set1,
                labels={"Registry": "", column_to_plot: ""},
            )
            fig.update_traces(opacity=0.9, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with cols_regs[1]:
            fig = px.pie(
                dset_reg.reset_index(),
                values=column_to_plot,
                names=cols.REGISTRY,
                title="",
                hole=0.4,
                color=cols.REGISTRY,
                color_discrete_sequence=px.colors.qualitative.Set1,
            )
            fig.update_traces(opacity=0.9, showlegend=False)
            fig.update_traces(
                textinfo="label+percent", textposition="auto", insidetextorientation="radial"
            )
            st.plotly_chart(fig, use_container_width=True)
