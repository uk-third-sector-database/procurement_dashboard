"""Module to handle DuckDB connection and caching."""

from datetime import date
from typing import Any

import duckdb
import pandas as pd
import streamlit as st

from gui import utils
from gui.content import TEXT
from utilities import shared
from utilities.columns import COLS, COLUMNS_TO_DISPLAY_SQL

VIEW_NAME = "data"
NULLS = "NULLS LAST"

@st.cache_resource
def get_con() -> duckdb.DuckDBPyConnection:
    """Get a cached DuckDB connection with the data loaded as a view.
        Use the connection in other functions with con = get_con()

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
def get_column_names() -> list[str]:
    """Get the column names of the data view.
    
    Returns:
        list[str]: A list of column names.
    """
    con = get_con()
    return [row[1] for row in con.execute(f"PRAGMA table_info('{VIEW_NAME}')").fetchall()]

@st.cache_data
def fetch_distinct_values(
    col_name: str, view: str = VIEW_NAME
) -> list[Any]:
    """
    Fetch distinct values from a column in a DuckDB view.

    Args:
        col_name: The column name in the data view.
        view: The view/table name (default VIEW_NAME).

    Returns:
        A list of distinct values from that column.
    """
    con = get_con()
    col_sql = quote_ident(col_name)
    df = con.execute(f"SELECT DISTINCT {col_sql} FROM {quote_ident(view)} ORDER BY 1").fetchdf()
    return df[col_name].tolist()

@st.cache_data
def fetch_date_range(
    col: str,
    view: str = VIEW_NAME,
) -> tuple[date | None, date | None]:
    """
    Fetch the minimum and maximum date from a column in a DuckDB view.

    Args:
        col: The column name (e.g. cols_sql.PAYMENT_DATE).
        view: The view/table name (default VIEW_NAME).

    Returns:
        A tuple (dmin, dmax) where either can be None if the column is empty.
    """
    con = get_con()
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

@st.cache_data
def fetch_nuts_level(
    level: int,
    where: str | None,
    params: list[str],
    order_by: str | None = None,
    view: str = VIEW_NAME,
) -> tuple[pd.DataFrame, list[str]]:
    """Fetch distinct (id, name) pairs for a NUTS level and return dataset & processed names.

    Args:
        level: NUTS level (0, 1, 2, or 3).
        where: Optional SQL WHERE clause (without the "WHERE" keyword).
        params: Optional list of parameters for the SQL query.
        order_by: Optional column name to order the results by (defaults to name column).
        view: The view/table name (default "data").

    Returns:
        A tuple (dataset, processed_names) where dataset is a DataFrame with columns
        [COLS[f"NUTS_ID_{level}"], COLS[f"NUTS_NAME_{level}"]] and processed_names is a list of
        cleaned-up names for display.
    Raises:
    """
    con = get_con()
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

@st.cache_data
def get_transactions_number(
    where_clause: str, params: list[str]
) -> int:
    """Get the number of transactions matching the given WHERE clause.
    Args:
        where_clause (str): The SQL WHERE clause.
        params (list[str]): The list of parameters for the SQL query.
    Returns:
        int: The number of transactions matching the WHERE clause.
    """
    con = get_con()
    row = con.execute(
        f"SELECT COUNT(*) FROM data WHERE {where_clause}",
        params,
    ).fetchone()
    assert row is not None, "COUNT(*) query returned no row"

    return row[0]

@st.cache_data
def get_suppliers_number(
    where_clause: str, params: list[str]
) -> int:
    """Get the number of suppliers matching the given WHERE clause.
    Args:
        where_clause (str): The SQL WHERE clause.
        params (list[str]): The list of parameters for the SQL query.
    Returns:
        int: The number of suppliers matching the WHERE clause.
    """
    con = get_con()
    row = con.execute(
        f"SELECT COUNT(DISTINCT {quote_ident(COLS['SUPPLIER'])}) FROM data WHERE {where_clause}",
        params,
    ).fetchone()
    assert row is not None, "COUNT(DISTINCT Supplier) query returned no row"

    return row[0]

@st.cache_data
def get_total_amount(where_clause: str, params: list[str]) -> float:
    """Get the total amount matching the given WHERE clause.
    Args:
        where_clause (str): The SQL WHERE clause.
        params (list[str]): The list of parameters for the SQL query.
    Returns:
        float: The total amount matching the WHERE clause.
    """
    con = get_con()
    row = con.execute(
        f"SELECT SUM({quote_ident(COLS['AMOUNT'])}) FROM data WHERE {where_clause}",
        params,
    ).fetchone()
    assert row is not None, "SUM(Amount) query returned no row"

    return row[0]

@st.cache_data
def get_raw_data( where_clause: str, params: list[str]
) -> pd.DataFrame:
    """Get the raw data matching the given WHERE clause, limited to the number of records
    specified in the state.
    Args:
        where_clause (str): The SQL WHERE clause (without the "WHERE" keyword).
        params (list[str]): The list of parameters for the SQL query.
    Returns:
        pd.DataFrame: The raw data matching the WHERE clause.
    """
    con = get_con()
    dset = con.execute(
        f"""
        SELECT {COLUMNS_TO_DISPLAY_SQL}
        FROM data
        WHERE {where_clause}
        ORDER BY {quote_ident(COLS["AMOUNT"])} DESC {NULLS}
        LIMIT ?
        """,
        params,
    ).fetchdf()

    if dset.empty:
        st.warning(TEXT["ERROR_NO_DATA"])
        st.stop()

    return dset
