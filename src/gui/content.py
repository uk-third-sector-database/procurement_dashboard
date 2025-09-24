"""Text and settings for the GUI."""

TEXT = {
    "APP_TITLE": "UK Third Sector Procurement Dashboard",
    "OPTION_NEITHER": "Do not apply filter",
    "ERROR_INCOMPLETE_DATE_RANGE": "Please select both start and end date.",
    "ERROR_INVALID_DATE_RANGE": "Start date must be before end date.",
    "ERROR_NO_SOURCE_SELECTED": "Please select at least one source.",
}

WIDGETS = {
    "RECORDS_TO_DISPLAY": {
        "label": "Transactions to display (up to)",
        "min_value": 10,
        "max_value": 500,
        "value": 250,
        "step": 10,
    },
    "DATE_RANGE": {
        "format": "DD/MM/YYYY",
    },
    "DATE_RANGE_RESET": {
        "label": "↺",
        "help": "Reset date range"
    }
}
