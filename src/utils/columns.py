"""Constants for column names used in the procurement dashboard application."""


def quote_ident(name: str) -> str:
    """
    Safely quote an identifier (column/table/view name) for SQL in DuckDB.
    Doubles internal quotes to prevent injection/SQL errors.
    """
    return '"' + name.replace('"', '""') + '"'


COLS = {
    "SOURCE": "Source",
    "DEPARTMENT": "Department",
    "AMOUNT": "Amount",
    "SUPPLIER": "Supplier",
    "PAYMENT_DATE": "Payment date",
    "PAYMENT_YEAR": "Payment year",
    "LATITUDE": "Latitude",
    "LONGITUDE": "Longitude",
    "GEOMETRY": "Geometry",
    "NUTS_ID_0": "NUTS ID 0",
    "NUTS_NAME_0": "NUTS Name 0",
    "NUTS_ID_1": "NUTS ID 1",
    "NUTS_NAME_1": "NUTS Name 1",
    "NUTS_ID_2": "NUTS ID 2",
    "NUTS_NAME_2": "NUTS Name 2",
    "NUTS_ID_3": "NUTS ID 3",
    "NUTS_NAME_3": "NUTS Name 3",
    "SPINE": "Is spine?",
    "MANUAL_MATCH": "Manual match to spine?",
    "OTHER_MATCH": "Other match to spine?",
    "REMOVED": "Removed?",
    "REMOVAL_DATE": "Removal date",
    # calculated columns
    "TOTAL_VALUE_PAYMENTS": "Total amount",
    "TOTAL_PAYMENTS": "Total transactions",
    "PAYMENTS": "Transactions",
    "VALUE": "Value",
    "DATE": "Date",
}

COLS_SQL = {k: quote_ident(v) for k, v in COLS.items()}

COLUMNS_TO_DISPLAY = [
    COLS["SOURCE"],
    COLS["DEPARTMENT"],
    COLS["AMOUNT"],
    COLS["SUPPLIER"],
    COLS["PAYMENT_DATE"],
    COLS["GEOMETRY"],
    COLS["SPINE"],
    COLS["MANUAL_MATCH"],
    COLS["OTHER_MATCH"],
    COLS["REMOVED"],
    COLS["REMOVAL_DATE"],
]
COLUMNS_DATE = [COLS["PAYMENT_DATE"], COLS["REMOVAL_DATE"]]
COLUMNS_TO_DISPLAY_SQL = ", ".join(quote_ident(c) for c in COLUMNS_TO_DISPLAY)

COLUMNS_TO_DISPLAY_STYLES = {
    COLS["AMOUNT"]: "{:,.0f}",
    COLS["TOTAL_VALUE_PAYMENTS"]: "{:,.0f}",
    COLS["TOTAL_PAYMENTS"]: "{:,.0f}",
}
