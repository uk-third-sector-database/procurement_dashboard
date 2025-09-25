"""Home page for the procurement dashboard app."""

from types import SimpleNamespace

import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st

import gui.db as db
import gui.sidebar as sd
import gui.widgets as wd
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

_state = st.session_state

cols = SimpleNamespace(**COLS)
cols_sql = SimpleNamespace(**COLS_SQL)
text = SimpleNamespace(**TEXT)
widgets = SimpleNamespace(**WIDGETS)


NULLS = "NULLS LAST"

st.set_page_config(
    layout="wide",
    page_title=text.APP_TITLE,
    page_icon=":receipt:",
    initial_sidebar_state="expanded",
)

# duckdb connection
con = db.get_con()

# sidebar top
sd.top()

# widgets
wd.records_number_selector()
wd.source_selector(con)
wd.payment_date_range_selector(con)
wd.is_removed_selector()
wd.is_spine_selector()

_state["DSET_NUTS"] = {1: None, 2: None, 3: None}
_state["NAMES_NUTS"] = {1: [], 2: [], 3: []}
_state["IDS_NUTS"] = {1: [], 2: [], 3: []}


wd.assign_state_nuts_keys(1)
if _state[wd.WIDGET_KEYS["IS_SPINE"]] is True:
    NUTS_LEVEL = 1
    _state["DSET_NUTS"][NUTS_LEVEL], _state["NAMES_NUTS"][NUTS_LEVEL] = db.fetch_nuts_level(
        con, level=NUTS_LEVEL, where=None, params=[]
    )
    wd.nuts_names_selector(NUTS_LEVEL)

    if _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][1]]:
        NUTS_LEVEL = 2
        PLACEHOLDERS = ", ".join("?" for _ in _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][1]])
        WHERE_CLAUSE = f"{quote_ident(COLS['NUTS_NAME_1'])} IN ({PLACEHOLDERS})"
        _state["DSET_NUTS"][NUTS_LEVEL], _state["NAMES_NUTS"][NUTS_LEVEL] = db.fetch_nuts_level(
            con=con,
            level=2,
            where=WHERE_CLAUSE,
            params=_state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][1]],
            order_by="NUTS_NAME_2",
        )
        wd.nuts_names_selector(NUTS_LEVEL)

        if _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][2]]:
            NUTS_LEVEL = 3
            PLACEHOLDERS = ", ".join(
                "?" for _ in _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][2]]
            )
            WHERE_CLAUSE = f"{quote_ident(COLS['NUTS_NAME_2'])} IN ({PLACEHOLDERS})"
            _state["DSET_NUTS"][NUTS_LEVEL], _state["NAMES_NUTS"][NUTS_LEVEL] = db.fetch_nuts_level(
                con=con,
                level=3,
                where=WHERE_CLAUSE,
                params=_state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][2]],
                order_by="NUTS_NAME_3",
            )

            wd.nuts_names_selector(NUTS_LEVEL)

    # manual and other match selectors
    wd.is_manual_match_selector()
    wd.is_other_match_selector()

else:
    _state[wd.WIDGET_KEYS["IS_MANUAL_MATCH"]] = None
    _state[wd.WIDGET_KEYS["IS_OTHER_MATCH"]] = None
    try:
        del _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][1]]
        del _state[wd.WIDGET_KEYS["NUTS_NAMES"]["ALL"][1]]
        del _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][2]]
        del _state[wd.WIDGET_KEYS["NUTS_NAMES"]["ALL"][2]]
        del _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][3]]
        del _state[wd.WIDGET_KEYS["NUTS_NAMES"]["ALL"][3]]
    except KeyError:
        pass


# build the WHERE clause and parameters
clauses, params = [], []

# source
PLACEHOLDERS = ", ".join("?" for _ in _state[wd.WIDGET_KEYS["SOURCE"]])
clauses.append(f"{cols_sql.SOURCE} IN ({PLACEHOLDERS})")
params.extend(_state[wd.WIDGET_KEYS["SOURCE"]])

try:
    if (
        _state[wd.WIDGET_KEYS["IS_SPINE"]] is True
        and _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][3]]
        and len(_state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][3]]) > 0
    ):
        PLACEHOLDERS = ", ".join("?" for _ in _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][3]])
        clauses.append(f"{cols_sql.NUTS_NAME_3} IN ({PLACEHOLDERS})")
        params.extend(_state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][3]])
except KeyError:
    pass

# is spine
if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not None:
    clauses.append(f"{cols_sql.SPINE} = ?")
    params.append(_state[wd.WIDGET_KEYS["IS_SPINE"]])

# is manual match
if _state[wd.WIDGET_KEYS["IS_MANUAL_MATCH"]] is not None:
    clauses.append(f"{cols_sql.MANUAL_MATCH} = ?")
    params.append(_state[wd.WIDGET_KEYS["IS_MANUAL_MATCH"]])

# is other match
if _state[wd.WIDGET_KEYS["IS_OTHER_MATCH"]] is not None:
    clauses.append(f"{cols_sql.OTHER_MATCH} = ?")
    params.append(_state[wd.WIDGET_KEYS["IS_OTHER_MATCH"]])

# is removed
if _state[wd.WIDGET_KEYS["IS_REMOVED"]] is not None:
    clauses.append(f"{cols_sql.REMOVED} = ?")
    params.append(_state[wd.WIDGET_KEYS["IS_REMOVED"]])

# date range
clauses.append(f"CAST({cols_sql.PAYMENT_DATE} AS DATE) BETWEEN ? AND ?")
params.extend(_state[wd.WIDGET_KEYS["PAYMENT_DATE_RANGE"]])

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

if _state[wd.WIDGET_KEYS["IS_SPINE"]] is None and n_transactions > 0:
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
    params + [_state[wd.WIDGET_KEYS["RECORDS_NUMBER"]]],
).fetchdf()

if dset_raw.empty:
    st.warning("No records available for the selected filters.")
    st.stop()

cols_metrics = st.columns(3)

with cols_metrics[0].container(border=True):
    if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True and n_suppliers_spine is not None:
        st.metric("🏬 Suppliers - all", f"{n_suppliers:,}")
        st.metric("Suppliers - spine (TSO)", f"{n_suppliers_spine:,}")
    else:
        st.metric("🏬 Suppliers", f"{n_suppliers:,}")
with cols_metrics[1].container(border=True):
    if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True and n_transactions_spine is not None:
        st.metric("🤝 Transactions - all", f"{n_transactions:,}")
        st.metric("Transactions - spine (TSO)", f"{n_transactions_spine:,}")
    else:
        st.metric("🤝 Transactions", f"{n_transactions:,}")
with cols_metrics[2].container(border=True):
    if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True and total_amount_spine is not None:
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
    if n_transactions > _state[wd.WIDGET_KEYS["RECORDS_NUMBER"]]:
        # more records available than displayed, inform the user about the display selection made
        st.write(f"""
        The top **{_state[wd.WIDGET_KEYS["RECORDS_NUMBER"]]}**
        selected transactions by **{cols.AMOUNT}**
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
            params + [_state[wd.WIDGET_KEYS["RECORDS_NUMBER"]]],
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
            params + [_state[wd.WIDGET_KEYS["RECORDS_NUMBER"]]],
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
    if not _state[wd.WIDGET_KEYS["IS_SPINE"]] or not all(
        [
            _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][1]],
            _state["IDS_NUTS"][1],
            _state["IDS_NUTS"][2],
            _state["IDS_NUTS"][3],
        ]
    ):
        st.info(
            f"""
            Geographical distribution is only available when filtering for
            '{cols.SPINE}' = True and valid selections for all the NUTS levels.
            """
        )
    else:
        nuts = gpd.read_file(shared.SHAPE_FILE).to_crs(epsg=4326)

        ids_1 = _state["IDS_NUTS"][1] or []
        ids_2 = _state["IDS_NUTS"][2] or []
        ids_3 = _state["IDS_NUTS"][3] or []

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
    if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True:
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
