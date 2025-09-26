"""Module for visualisations in the app."""

import pandas as pd
import streamlit as st

import gui.widgets as wd
from gui import db
from gui.content import TEXT, WIDGETS
from utilities.columns import COLS_SQL, COLUMNS_DATE, COLUMNS_TO_DISPLAY_STYLES

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

    cols_metrics = st.columns(3)

    with cols_metrics[0].container(border=True):
        metric_content = WIDGETS["METRICS"]["SUPPLIERS"]
        if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True:
            st.metric(**metric_content["ALL"], value=f"{n_suppliers:,}")
            st.metric(**metric_content["SPINE"], value=f"{n_suppliers_spine:,}")
        else:
            st.metric(**metric_content["SPINE"], value=f"{n_suppliers:,}")
    with cols_metrics[1].container(border=True):
        metric_content = WIDGETS["METRICS"]["TRANSACTIONS"]
        if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True:
            st.metric(**metric_content["ALL"], value=f"{n_transactions:,}")
            st.metric(**metric_content["SPINE"], value=f"{n_transactions_spine:,}")
        else:
            st.metric(**metric_content["SPINE"], value=f"{n_transactions:,}")
    with cols_metrics[2].container(border=True):
        metric_content = WIDGETS["METRICS"]["AMOUNT"]
        if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True:
            st.metric(**metric_content["ALL"], value=f"{total_amount:,.0f}")
            st.metric(**metric_content["SPINE"], value=f"{total_amount_spine:,.0f}")
        else:
            st.metric(**metric_content["SPINE"], value=f"{total_amount:,.0f}")


def display_raw_data(where_clause: str, params: list[str]) -> None:
    """Retrieve and display the raw data in a table.

    Args:
        where_clause (str): The SQL WHERE clause.
        params (list[str]): The list of parameters for the SQL query.
    """
    wd.records_number_selector()
    dset_raw = db.get_raw_data(
        where_clause, params + [_state[wd.WIDGET_KEYS["RECORDS_NUMBER"]]]
    )

    # format the columns to display
    for col in COLUMNS_DATE:
        if col in dset_raw.columns and pd.api.types.is_datetime64_any_dtype(dset_raw[col]):
            dset_raw[col] = dset_raw[col].dt.strftime("%d/%m/%Y")
    dset_styled = dset_raw.style.format(COLUMNS_TO_DISPLAY_STYLES)
    st.dataframe(dset_styled, use_container_width=True, hide_index=True)
