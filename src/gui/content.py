"""Text and settings for the GUI."""

EMOJIS = {
    "INFO": "ⓘ",
    "WARNING": "⚠",
    "SUPPLIERS": "🏬",
    "TRANSACTIONS": "🤝",
    "AMOUNT": "💷"
}

TEXT = {
    "APP_TITLE": "UK Third Sector Procurement Dashboard",
    "OPTION_NEITHER": "Do not apply filter",
    "ERROR_INCOMPLETE_DATE_RANGE": f"{EMOJIS['WARNING']}Please select both start and end date.",
    "ERROR_INVALID_DATE_RANGE": f"{EMOJIS['WARNING']}Start date must be before end date.",
    "ERROR_NO_SOURCE_SELECTED": f"{EMOJIS['WARNING']}Please select at least one source.",
    "ERROR_INCOMPLETE_SELECTIONS": f"{EMOJIS['WARNING']} Please complete all selections.",
    "ERROR_NO_DATA": f"{EMOJIS['WARNING']}No data matches the selected filters.",
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
    "DATE_RANGE_RESET": {"label": "↺", "help": "Reset date range"},
    "IS_REMOVED": {"label": "Is removed?"},
    "IS_SPINE": {"label": "Is spine?"},
    "IS_MANUAL_MATCH": {"label": "Manual match to spine?"},
    "IS_OTHER_MATCH": {"label": "Other match to spine?"},
    "NUTS_NAMES": {"ALL": {"label": "All"}},
    "METRICS": {
        "SUPPLIERS": {
            "ALL": {"label": f"{EMOJIS['SUPPLIERS']} All suppliers"},
            "SPINE": {"label": "TSOs"},
        },
        "TRANSACTIONS": {
            "ALL": {"label": f"{EMOJIS['TRANSACTIONS']} All transactions"},
            "SPINE": {"label": "Transactions with TSOs"},
        },
        "AMOUNT": {
            "ALL": {"label": f"{EMOJIS['AMOUNT']} Total amount"},
            "SPINE": {"label": "Amount to TSOs"},
        }
    }
}
