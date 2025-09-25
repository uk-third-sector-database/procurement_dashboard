"""Text and settings for the GUI."""

TEXT = {
    "APP_TITLE": "UK Third Sector Procurement Dashboard",
    "OPTION_NEITHER": "Do not apply filter",
    "ERROR_INCOMPLETE_DATE_RANGE": "Please select both start and end date.",
    "ERROR_INVALID_DATE_RANGE": "Start date must be before end date.",
    "ERROR_NO_SOURCE_SELECTED": "Please select at least one source.",
}

WIDGETS = {
    "RECORDS_NUMBER": {
        "label": "Transactions to display (up to)",
        "min_value": 10,
        "max_value": 500,
        "value": 250,
        "step": 10,
    },
    "SOURCES": {
        "label": "Payment sources",
    },
    "DATE_RANGE": {
        "label": "Payment date",
        "format": "DD/MM/YYYY",
    },
    "DATE_RANGE_RESET": {
        "label": "↺",
        "help": "Reset date range"
    },
    "IS_REMOVED": {
        "label": "Is removed?"
    },
    "IS_SPINE": {
        "label": "Is spine?"
    },
    "IS_MANUAL_MATCH": {
        "label": "Manual match to spine?"
    },
    "IS_OTHER_MATCH": {
        "label": "Other match to spine?"
    },
}
