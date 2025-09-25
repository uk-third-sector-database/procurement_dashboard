"""Control widgets for the app."""

from types import SimpleNamespace

import duckdb
import streamlit as st

import gui.db as db
from gui.content import TEXT, WIDGETS
from utilities.columns import COLS, quote_ident

_state = st.session_state

WIDGET_KEYS = {
    "RECORDS_NUMBER": "input_records_number",
    "SOURCE": "multiselect_source",
    "PAYMENT_DATE_RANGE": "input_payment_date_range",
    "IS_REMOVED": "selectbox_is_removed",
    "IS_SPINE": "selectbox_is_spine",
    "IS_MANUAL_MATCH": "selectbox_is_manual_match",
    "IS_OTHER_MATCH": "selectbox_is_other_match",
}
cols = SimpleNamespace(**COLS)
text = SimpleNamespace(**TEXT)
widgets = SimpleNamespace(**WIDGETS)


def records_number_selector() -> None:
    """Render the records number selector widget in the sidebar."""
    st.sidebar.number_input(**widgets.RECORDS_NUMBER, key=WIDGET_KEYS["RECORDS_NUMBER"])


def source_selector(con: duckdb.DuckDBPyConnection) -> None:
    """Render the source selector widget in the sidebar. Stops the app if no source is selected.

    Args:
        con (duckdb.DuckDBPyConnection): A DuckDB connection with the data view created.
    """
    sources = db.fetch_distinct_values(con, cols.SOURCE)
    st.sidebar.multiselect(
        **widgets.SOURCES, options=sources, default=sources, key=WIDGET_KEYS["SOURCE"]
    )
    if not _state[WIDGET_KEYS["SOURCE"]]:
        st.sidebar.warning(text.ERROR_NO_SOURCE_SELECTED)
        st.stop()


def payment_date_range_selector(con: duckdb.DuckDBPyConnection) -> None:
    """Render the payment date range selector widget in the sidebar.
        Stops the app if the date range is incomplete or invalid.
    Args:
        con (duckdb.DuckDBPyConnection): A DuckDB connection with the data view created.
    """
    dmin, dmax = db.fetch_date_range(con, quote_ident(cols.PAYMENT_DATE))
    if WIDGET_KEYS["PAYMENT_DATE_RANGE"] not in _state:
        _state[WIDGET_KEYS["PAYMENT_DATE_RANGE"]] = (dmin, dmax)
    dcols = st.sidebar.columns([7, 1], vertical_alignment="bottom")
    with dcols[1]:
        if st.button(**widgets.DATE_RANGE_RESET):
            _state[WIDGET_KEYS["PAYMENT_DATE_RANGE"]] = (dmin, dmax)
    with dcols[0]:
        dcols[0].date_input(
            **widgets.DATE_RANGE,
            min_value=dmin,
            max_value=dmax,
            key=WIDGET_KEYS["PAYMENT_DATE_RANGE"],
        )
    if not (
        isinstance(_state[WIDGET_KEYS["PAYMENT_DATE_RANGE"]], tuple | list)
        and len(_state[WIDGET_KEYS["PAYMENT_DATE_RANGE"]]) == 2
    ):
        st.sidebar.warning(text.ERROR_INCOMPLETE_DATE_RANGE)
        st.stop()
    else:
        start_date, end_date = _state[WIDGET_KEYS["PAYMENT_DATE_RANGE"]]
        if start_date > end_date:
            st.sidebar.warning(text.ERROR_INVALID_DATE_RANGE)
            st.stop()


def is_removed_selector() -> None:
    """Render the is removed selector widget in the sidebar."""
    st.sidebar.selectbox(
        **widgets.IS_REMOVED,
        options=[None, True, False],
        format_func=lambda x: text.OPTION_NEITHER if x is None else str(x),
        key=WIDGET_KEYS["IS_REMOVED"],
    )


def is_spine_selector() -> None:
    """Render the is spine selector widget in the sidebar."""
    st.sidebar.selectbox(
        **widgets.IS_SPINE,
        options=[None, True, False],
        format_func=lambda x: text.OPTION_NEITHER if x is None else str(x),
        key=WIDGET_KEYS["IS_SPINE"],
    )

def is_manual_match_selector() -> None:
    """Render the is manual match selector widget in the sidebar."""
    st.sidebar.selectbox(
        **widgets.IS_MANUAL_MATCH,
        options=[None, True, False],
        format_func=lambda x: text.OPTION_NEITHER if x is None else str(x),
        key=WIDGET_KEYS["IS_MANUAL_MATCH"],
    )

def is_other_match_selector() -> None:
    """Render the is other match selector widget in the sidebar."""
    st.sidebar.selectbox(
        **widgets.IS_OTHER_MATCH,
        options=[None, True, False],
        format_func=lambda x: text.OPTION_NEITHER if x is None else str(x),
        key=WIDGET_KEYS["IS_OTHER_MATCH"],
    )
