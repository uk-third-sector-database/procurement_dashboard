"""Utility functions for the GUI."""

import utils.shared as shared


def process_nuts_names(nuts_names):
    """Ensure that the NULL_TEXT value is at the end of the list.

    Args:
        nuts_names (list): List of NUTS names.
    Returns:
        list: Processed list of NUTS names.
    """

    if shared.NULL_TEXT in nuts_names:
        nuts_names.remove(shared.NULL_TEXT)
        nuts_names.append(shared.NULL_TEXT)

    return nuts_names
