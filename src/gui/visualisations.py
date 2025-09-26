"""Module for visualisations in the app."""

import pandas as pd
import plotly.express as px
import streamlit as st

import gui.widgets as wd
from gui import db
from gui.content import TEXT, WIDGETS
from utilities.columns import (
    COLS,
    COLS_SQL,
    COLUMNS_DATE,
    COLUMNS_TO_DISPLAY_STYLES,
    REGISTRIES,
    quote_ident,
)

_state = st.session_state


def display_top_metrics(where_clause: str, params: list[str]):
    """Retrieve and display the top metrics in the app sidebar.
    Args:
        where_clause (str): The SQL WHERE clause.
        params (list[str]): The list of parameters for the SQL query.
    """

    n_transactions = db.get_transactions_number(where_clause, params)
    if n_transactions == 0:
        st.warning(TEXT["ERROR_NO_DATA"])
        st.stop()
    n_suppliers = db.get_suppliers_number(where_clause, params)
    total_amount = db.get_total_amount(where_clause, params)

    if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True:
        where_clause_spine = where_clause + f" AND {COLS_SQL['SPINE']} = TRUE"
        n_suppliers_spine = db.get_suppliers_number(where_clause_spine, params)
        n_transactions_spine = db.get_transactions_number(where_clause_spine, params)
        total_amount_spine = db.get_total_amount(where_clause_spine, params)
    else:
        n_suppliers_spine = None
        n_transactions_spine = None
        total_amount_spine = None

    cols_metrics = st.columns(3)

    with cols_metrics[0].container(border=True):
        metric_content = WIDGETS["METRICS"]["SUPPLIERS"]
        match _state[wd.WIDGET_KEYS["IS_SPINE"]]:
            case True:
                st.metric(**metric_content["SPINE"], value=f"{n_suppliers:,}")
            case False:
                st.metric(**metric_content["NON_SPINE"], value=f"{n_suppliers:,}")
            case None:
                st.metric(**metric_content["ALL"], value=f"{n_suppliers:,}")
                st.metric(**metric_content["SPINE"], value=f"{n_suppliers_spine:,}")

    with cols_metrics[1].container(border=True):
        metric_content = WIDGETS["METRICS"]["TRANSACTIONS"]
        match _state[wd.WIDGET_KEYS["IS_SPINE"]]:
            case True:
                st.metric(**metric_content["SPINE"], value=f"{n_transactions:,}")
            case False:
                st.metric(**metric_content["NON_SPINE"], value=f"{n_transactions:,}")
            case None:
                st.metric(**metric_content["ALL"], value=f"{n_transactions:,}")
                st.metric(**metric_content["SPINE"], value=f"{n_transactions_spine:,}")
    with cols_metrics[2].container(border=True):
        metric_content = WIDGETS["METRICS"]["AMOUNT"]
        match _state[wd.WIDGET_KEYS["IS_SPINE"]]:
            case True:
                st.metric(**metric_content["SPINE"], value=f"{total_amount:,}")
            case False:
                st.metric(**metric_content["NON_SPINE"], value=f"{total_amount:,}")
            case None:
                st.metric(**metric_content["ALL"], value=f"{total_amount:,}")
                st.metric(**metric_content["SPINE"], value=f"{total_amount_spine:,}")


def display_raw_data(where_clause: str, params: list[str]) -> None:
    """Retrieve and display the raw data in a table.

    Args:
        where_clause (str): The SQL WHERE clause.
        params (list[str]): The list of parameters for the SQL query.
    """
    wd.transactions_number_selector()
    dset_raw = db.get_raw_data(
        where_clause, params + [_state[wd.WIDGET_KEYS["TRANSACTIONS_NUMBER"]]]
    )

    # format the columns to display
    for col in COLUMNS_DATE:
        if col in dset_raw.columns and pd.api.types.is_datetime64_any_dtype(dset_raw[col]):
            dset_raw[col] = dset_raw[col].dt.strftime("%d/%m/%Y")
    dset_styled = dset_raw.style.format(COLUMNS_TO_DISPLAY_STYLES)
    st.dataframe(dset_styled, use_container_width=True, hide_index=True)


def display_suppliers(where_clause: str, params: list[str]) -> None:
    """Retrieve and display the suppliers ranking in a table.
    Args:
        where_clause (str): The SQL WHERE clause.
        params (list[str]): The list of parameters for the SQL query.
    """
    sel_cols = st.columns(2)
    with sel_cols[0]:
        wd.suppliers_ranking_selector()
    with sel_cols[1]:
        wd.suppliers_number_selector()

    if _state[wd.WIDGET_KEYS["SUPPLIERS_RANKING"]] == COLS["TOTAL_VALUE_PAYMENTS"]:
        order_by = COLS_SQL["TOTAL_VALUE_PAYMENTS"]
    else:
        order_by = COLS_SQL["TOTAL_PAYMENTS"]
    sql = f"""
                WITH filtered AS (
                    SELECT {COLS_SQL["SUPPLIER"]},
                            {COLS_SQL["AMOUNT"]}
                FROM data
                WHERE {where_clause}
                ),
                agg AS (
                    SELECT
                        {COLS_SQL["SUPPLIER"]},
                        SUM({COLS_SQL["AMOUNT"]}) AS {COLS_SQL["TOTAL_VALUE_PAYMENTS"]},
                        COUNT(*) AS {COLS_SQL["TOTAL_PAYMENTS"]}
                    FROM filtered
                    GROUP BY {COLS_SQL["SUPPLIER"]}
                )
                SELECT *
                FROM agg
                ORDER BY {order_by} DESC NULLS LAST
                LIMIT ?
            """
    params = params + [_state[wd.WIDGET_KEYS["SUPPLIERS_NUMBER"]]]
    dset = db.run_query(sql, params)

    st.dataframe(
        dset.style.format(COLUMNS_TO_DISPLAY_STYLES),
        use_container_width=False,
        hide_index=True,
    )


def display_timecourses(where_clause: str, params: list[str]) -> None:
    """Retrieve and display the timecourses in a bar chart.
    Args:
        where_clause (str): The SQL WHERE clause.
        params (list[str]): The list of parameters for the SQL query.
    """
    column_date = COLS["DATE"]
    column_transactions = COLS["PAYMENTS"]
    column_value = COLS["VALUE"]
    sql = f"""
        SELECT
            strftime({quote_ident(COLS["PAYMENT_DATE"])}, '%Y-%m') AS {quote_ident(column_date)},
            COUNT(*) AS {quote_ident(column_transactions)},
            SUM({quote_ident(COLS["AMOUNT"])}) AS {quote_ident(column_value)}
        FROM data
        WHERE {where_clause}
        GROUP BY {quote_ident(column_date)}
        ORDER BY {quote_ident(column_date)}
        """

    dset = db.run_query(sql, params)
    dset[column_date] = pd.to_datetime(dset[column_date])
    sel_cols = st.columns(2)
    with sel_cols[0]:
        wd.timecourses_data_selector([column_transactions, column_value])
    with sel_cols[1]:
        wd.timecourses_format_selector(WIDGETS["TIMECOURSES"]["FORMATS"])

    if _state[wd.WIDGET_KEYS["TIMECOURSES_FORMAT"]] == WIDGETS["TIMECOURSES"]["FORMATS"][0]:
        fig = px.bar(
            dset,
            x=column_date,
            y=_state[wd.WIDGET_KEYS["TIMECOURSES_DATA"]],
            labels={column_date: ""},
            title="",
        )
    else:
        fig = px.line(
            dset,
            x=column_date,
            y=_state[wd.WIDGET_KEYS["TIMECOURSES_DATA"]],
            labels={column_date: ""},
            title="",
        )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 40, "b": 0})
    fig.update_yaxes(tickformat=",")
    fig.update_xaxes(dtick="M12", tickformat="%b %Y", ticklabelmode="period")

    st.plotly_chart(fig, use_container_width=True)


def display_geographical_distribution(where_clause: str, params: list[str]) -> None:
    """Retrieve and display the geographical distribution in a choropleth map.
    Args:
        where_clause (str): The SQL WHERE clause.
        params (list[str]): The list of parameters for the SQL query.
    """
    gpd = db.get_shape_file()
    col_sels = st.columns(2, vertical_alignment="bottom")

    if _state[wd.WIDGET_KEYS["FILTER_NUTS"]] is True:
        ids_1 = _state["IDS_NUTS"][1] or []
        ids_2 = _state["IDS_NUTS"][2] or []
        ids_3 = _state["IDS_NUTS"][3] or []

        mask = (
            (gpd["LEVL_CODE"].eq(1) & gpd["NUTS_ID"].isin(ids_1))
            | (gpd["LEVL_CODE"].eq(2) & gpd["NUTS_ID"].isin(ids_2))
            | (gpd["LEVL_CODE"].eq(3) & gpd["NUTS_ID"].isin(ids_3))
        )

        nuts = gpd[mask].copy()
        # retrieve the nuts level 3 data for the selected NUTS
        nuts_level = 3
        with col_sels[0]:
            wd.geographical_distribution_data_selector(
                [COLS["TOTAL_PAYMENTS"], COLS["TOTAL_VALUE_PAYMENTS"]]
            )
    else:
        # select data from UK
        nuts = gpd[gpd["CNTR_CODE"] == "UK"].copy()
        with col_sels[0]:
            cols_refine = st.columns(2)
            with cols_refine[0]:
                wd.geographical_distribution_data_selector(
                    [COLS["TOTAL_PAYMENTS"], COLS["TOTAL_VALUE_PAYMENTS"]]
                )
            with cols_refine[1]:
                wd.nuts_level_selector()
                nuts_level = _state[wd.WIDGET_KEYS["NUTS_LEVEL"]]

    nuts_display = nuts.loc[nuts.LEVL_CODE == nuts_level]
    column_nuts_id = f"NUTS ID {nuts_level}"
    sql = f"""


            WITH filtered AS (
                SELECT {quote_ident(column_nuts_id)},
                        {COLS_SQL["AMOUNT"]}
            FROM data
            WHERE {where_clause}
            ),
            agg AS (
                SELECT
                    {quote_ident(column_nuts_id)},
                    SUM({COLS_SQL["AMOUNT"]}) AS {COLS_SQL["TOTAL_VALUE_PAYMENTS"]},
                    COUNT(*) AS {COLS_SQL["TOTAL_PAYMENTS"]}
                FROM filtered
                WHERE {quote_ident(column_nuts_id)} IS NOT NULL
                GROUP BY {quote_ident(column_nuts_id)}
            )
            SELECT *
            FROM agg
        """
    dset = db.run_query(sql, params)

    sql = f"""


            WITH filtered AS (
                SELECT {quote_ident(column_nuts_id)},
                        {COLS_SQL["AMOUNT"]}
            FROM data
            WHERE {where_clause}
            ),
            agg AS (
                SELECT
                    {quote_ident(column_nuts_id)},
                    SUM({COLS_SQL["AMOUNT"]}) AS {COLS_SQL["TOTAL_VALUE_PAYMENTS"]},
                    COUNT(*) AS {COLS_SQL["TOTAL_PAYMENTS"]}
                FROM filtered
                WHERE {quote_ident(column_nuts_id)} IS NULL
                GROUP BY {quote_ident(column_nuts_id)}
            )
            SELECT *
            FROM agg
        """

    dset_no_nuts = db.run_query(sql, params)

    # merge nuts_display with dset_nuts on NUTS_ID_1
    nuts_display = nuts_display.merge(dset, how="left", left_on="NUTS_ID", right_on=column_nuts_id)
    nuts_display[COLS["TOTAL_VALUE_PAYMENTS"]] = nuts_display[COLS["TOTAL_VALUE_PAYMENTS"]].fillna(
        0
    )
    nuts_display[COLS["TOTAL_PAYMENTS"]] = nuts_display[COLS["TOTAL_PAYMENTS"]].fillna(0)
    nuts_display.set_index("NUTS_ID", inplace=True)
    with col_sels[1]:
        wd.popover_dataset(
            WIDGETS["GEOGRAPHICAL_DISTRIBUTION"]["LEGEND"]["label"], nuts_display[["NUTS_NAME"]]
        )

    cols_maps = st.columns(2)
    with cols_maps[0]:
        fig = px.choropleth(
            nuts_display,
            geojson=nuts_display.geometry,
            locations=nuts_display.index,
            hover_name="NUTS_NAME",
            color=_state[wd.WIDGET_KEYS["GEOGRAPHICAL_DISTRIBUTION_DATA"]],
            color_continuous_scale=WIDGETS["GEOGRAPHICAL_DISTRIBUTION"]["MAP"]["colorscale"],
            projection="mercator",
        )

        fig.update_geos(fitbounds="locations", visible=False)

        fig.update_layout(
            margin={"l": 0, "r": 0, "t": 20, "b": 0},
        )

        fig.update_layout(
            coloraxis_colorbar={
                "orientation": "h",
                "x": 0.5,
                "xanchor": "center",
                "y": 1.05,
                "yanchor": "bottom",
            }
        )

        st.plotly_chart(fig, use_container_width=True)
    with cols_maps[1]:
        st.dataframe(
            nuts_display[[COLS["TOTAL_PAYMENTS"], COLS["TOTAL_VALUE_PAYMENTS"]]],
            use_container_width=True,
            hide_index=False,
        )
        if not dset_no_nuts.empty:
            st.text(TEXT["TITLE_DATA_NO_NUTS_ID"])
            st.dataframe(
                dset_no_nuts.style.format(COLUMNS_TO_DISPLAY_STYLES),
                use_container_width=False,
                hide_index=True,
            )


def display_registry_distribution(where_clause: str, params: list[str]) -> None:
    """Retrieve and display the registry distribution in bar and pie charts.
    Args:
        where_clause (str): The SQL WHERE clause.
        params (list[str]): The list of parameters for the SQL query.
    """
    dset_reg = pd.DataFrame()
    for registry in REGISTRIES:
        col_flag = quote_ident(registry)
        col_amount = COLS_SQL["AMOUNT"]

        sql = f"""
                SELECT
                    COUNT_IF({col_flag}) AS {COLS_SQL["TOTAL_PAYMENTS"]},
                    SUM(CASE WHEN {col_flag} THEN {col_amount} ELSE 0 END)
                      AS {COLS_SQL["TOTAL_VALUE_PAYMENTS"]}
                FROM data
                WHERE {where_clause}
            """
        dset = db.run_query(sql, params)
        dset.index = [registry]
        dset_reg = pd.concat([dset_reg, dset], axis=0)

    dset_reg.index.name = COLS["REGISTRY"]
    dset_reg["Name"] = dset_reg.index.map(REGISTRIES)
    dset_reg = dset_reg[["Name", COLS["TOTAL_PAYMENTS"], COLS["TOTAL_VALUE_PAYMENTS"]]]

    cols_selections = st.columns([0.2, 0.8])
    with cols_selections[0]:
        wd.registries_distribution_data_selector(
            [COLS["TOTAL_PAYMENTS"], COLS["TOTAL_VALUE_PAYMENTS"]]
        )
    with cols_selections[1]:
        wd.popover_dataset(
            WIDGETS["REGISTRIES"]["VIEW"]["label"],
            dset_reg.reset_index().rename(columns={"Registry": "Code"}).set_index("Code"),
        )

    cols_regs = st.columns(2)
    with cols_regs[0]:
        fig = px.bar(
            dset_reg.reset_index(),
            y=COLS["REGISTRY"],
            x=_state[wd.WIDGET_KEYS["REGISTRIES_DATA"]],
            title="",
            orientation="h",
            color=COLS["REGISTRY"],
            color_discrete_sequence=px.colors.qualitative.Set1,
            labels={
                "Registry": "",
            },
        )

        fig.update_traces(opacity=0.9, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with cols_regs[1]:
        fig = px.pie(
            dset_reg.reset_index(),
            values=_state[wd.WIDGET_KEYS["REGISTRIES_DATA"]],
            names=COLS["REGISTRY"],
            title="",
            hole=0.4,
            color=COLS["REGISTRY"],
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        fig.update_traces(opacity=0.9, showlegend=False)
        fig.update_traces(
            textinfo="label+percent", textposition="auto", insidetextorientation="radial"
        )
        st.plotly_chart(fig, use_container_width=True)
