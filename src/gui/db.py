"""Module to handle DuckDB connection and caching."""

from datetime import date
from typing import Any

import duckdb
import pandas as pd
import streamlit as st

import utilities.shared as shared
import gui.utils as utils
from utilities.columns import COLS

VIEW_NAME = "data"


@st.cache_resource
def get_con() -> duckdb.DuckDBPyConnection:
    """Get a cached DuckDB connection with the data loaded as a view.

    Returns:
        duckdb.DuckDBPyConnection: A DuckDB connection with the data view created.
    """
    con = duckdb.connect()
    rel = con.read_parquet(str(shared.FILEPATH))
    rel.create_view(VIEW_NAME, replace=True)

    return con


def quote_ident(name: str) -> str:
    """
    Safely quote an identifier (column/table/view name) for SQL in DuckDB.
    Doubles internal quotes to prevent injection/SQL errors.

    Args:
        name (str): The identifier to quote.
    Returns:
        str: The safely quoted identifier.
    """
    return '"' + name.replace('"', '""') + '"'

@st.cache_data
def get_column_names(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Get the column names of the data view.
    Args:
        con (duckdb.DuckDBPyConnection): A DuckDB connection with the data view created.
    Returns:
        list[str]: A list of column names.
    """
    return [row[1] for row in con.execute(f"PRAGMA table_info('{VIEW_NAME}')").fetchall()]


def fetch_distinct_values(
    con: duckdb.DuckDBPyConnection, col_name: str, view: str = VIEW_NAME
) -> list[Any]:
    """
    Fetch distinct values from a column in a DuckDB view.

    Args:
        con: DuckDB connection.
        col_name: The column name in the data view.
        view: The view/table name (default VIEW_NAME).

    Returns:
        A list of distinct values from that column.
    """
    col_sql = quote_ident(col_name)
    df = con.execute(f"SELECT DISTINCT {col_sql} FROM {quote_ident(view)} ORDER BY 1").fetchdf()
    return df[col_name].tolist()


def fetch_date_range(
    con: duckdb.DuckDBPyConnection,
    col: str,
    view: str = VIEW_NAME,
) -> tuple[date | None, date | None]:
    """
    Fetch the minimum and maximum date from a column in a DuckDB view.

    Args:
        con: DuckDB connection.
        col: The column name (e.g. cols_sql.PAYMENT_DATE).
        view: The view/table name (default VIEW_NAME).

    Returns:
        A tuple (dmin, dmax) where either can be None if the column is empty.
    """
    row = con.execute(
        f"""
        SELECT
            MIN(CAST({col} AS DATE)),
            MAX(CAST({col} AS DATE))
        FROM {view}
        """
    ).fetchone()
    assert row is not None, f"Failed to retrieve date range for {col}"
    return row[0], row[1]


def fetch_nuts_level(
    con: duckdb.DuckDBPyConnection,
    level: int,
    where: str | None,
    params: list[str],
    order_by: str | None = None,
    view: str = VIEW_NAME,
) -> tuple[pd.DataFrame, list[str]]:
    """Fetch distinct (id, name) pairs for a NUTS level and return dataset + processed names.
    
    Args:
        con: DuckDB connection.
        level: NUTS level (0, 1, 2, or 3).
        where: Optional SQL WHERE clause (without the "WHERE" keyword).
        params: Optional list of parameters for the SQL query.
        order_by: Optional column name to order the results by (defaults to name column).
        view: The view/table name (default "data").
    """

    col_id = quote_ident(COLS[f"NUTS_ID_{level}"])
    col_name = quote_ident(COLS[f"NUTS_NAME_{level}"])
    order_col = quote_ident(COLS[order_by]) if order_by else col_name

    sql = f"""
        SELECT DISTINCT {col_id} AS id, {col_name} AS name
        FROM {view}
        {"WHERE " + where if where else ""}
        ORDER BY {order_col}
    """

    dset = con.execute(sql, params).fetchdf()
    dset.columns = [COLS[f"NUTS_ID_{level}"], COLS[f"NUTS_NAME_{level}"]]

    return dset, utils.process_nuts_names(dset[COLS[f"NUTS_NAME_{level}"]].tolist())
