"""Module for visualisations in the app."""

import duckdb
import streamlit as st

import gui.db as db
import gui.widgets as wd
from gui.content import WIDGETS
from utilities.columns import COLS_SQL

_state = st.session_state


def display_top_metrics(con: duckdb.DuckDBPyConnection, where_clause: str, params: list[str]):
    """Display the top metrics in the app sidebar."""

    n_transactions = db.get_transactions_number(con, where_clause, params)
    n_suppliers = db.get_suppliers_number(con, where_clause, params)
    total_amount = db.get_total_amount(con, where_clause, params)

    if _state[wd.WIDGET_KEYS["IS_SPINE"]] is None and n_transactions > 0:
        where_clause_spine = where_clause + f" AND {COLS_SQL['SPINE']} = TRUE"
        n_suppliers_spine = db.get_suppliers_number(con, where_clause_spine, params)
        n_transactions_spine = db.get_transactions_number(con, where_clause_spine, params)
        total_amount_spine = db.get_total_amount(con, where_clause_spine, params)
    else:
        n_suppliers_spine: int | None = None
        n_transactions_spine: int | None = None
        total_amount_spine: float | None = None

    cols_metrics = st.columns(3)

    with cols_metrics[0].container(border=True):
        metric_content = WIDGETS["METRICS"]["SUPPLIERS"]
        if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True and n_suppliers_spine is not None:
            st.metric(**metric_content["ALL"], value=f"{n_suppliers:,}")
            st.metric(**metric_content["SPINE"], value=f"{n_suppliers_spine:,}")
        else:
            st.metric(**metric_content["SPINE"], value=f"{n_suppliers:,}")
    with cols_metrics[1].container(border=True):
        metric_content = WIDGETS["METRICS"]["TRANSACTIONS"]
        if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True and n_transactions_spine is not None:
            st.metric(**metric_content["ALL"], value=f"{n_transactions:,}")
            st.metric(**metric_content["SPINE"], value=f"{n_transactions_spine:,}")
        else:
            st.metric(**metric_content["SPINE"], value=f"{n_transactions:,}")
    with cols_metrics[2].container(border=True):
        metric_content = WIDGETS["METRICS"]["AMOUNT"]
        if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True and total_amount_spine is not None:
            st.metric(**metric_content["ALL"], value=f"{total_amount:,.0f}")
            st.metric(**metric_content["SPINE"], value=f"{total_amount_spine:,.0f}")
        else:
            st.metric(**metric_content["SPINE"], value=f"{total_amount:,.0f}")
