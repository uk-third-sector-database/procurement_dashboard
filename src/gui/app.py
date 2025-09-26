"""Home page for the procurement dashboard app."""

from types import SimpleNamespace

import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st

import gui.sidebar as sd
import gui.visualisations as vis
import gui.widgets as wd
from gui import db
from gui.content import TEXT, WIDGETS
from utilities import shared
from utilities.columns import (
    COLS,
    COLS_SQL,
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
wd.source_selector()
wd.payment_date_range_selector()
wd.is_removed_selector()
wd.is_spine_selector()

wd.init_nuts_state_vars()
wd.assign_state_nuts_keys(1)
if _state[wd.WIDGET_KEYS["IS_SPINE"]] is True:
    # manual and other match selectors
    wd.is_manual_match_selector()
    wd.is_other_match_selector()

    # NUTS selectors
    wd.nuts_names_selector(1)
    if _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][1]]:
        wd.nuts_names_selector(2)

        if _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][2]]:
            wd.nuts_names_selector(3)
            if not _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][3]]:
                st.warning(text.ERROR_INCOMPLETE_SELECTIONS)
                st.stop()
        else:
            st.warning(text.ERROR_INCOMPLETE_SELECTIONS)
            st.stop()
    else:
        st.warning(text.ERROR_INCOMPLETE_SELECTIONS)
        st.stop()
else:
    wd.reset_is_spine_state_vars()

where_clause, params = wd.build_where_clause_and_params()

vis.display_top_metrics(where_clause, params)

titles = widgets.VIEW_TABS["COMMON"].copy()
if _state[wd.WIDGET_KEYS["IS_SPINE"]] is True:
    titles += widgets.VIEW_TABS["SPINE"]
tabs_views = st.tabs(titles)

with tabs_views[0]:
    vis.display_raw_data(where_clause, params)

with tabs_views[1]:
    vis.display_suppliers(where_clause, params)

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
        WHERE {where_clause}
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

if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True:
    st.stop()
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
                WHERE {where_clause}
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
                    WHERE {where_clause}
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
