"""Home page for the procurement dashboard app."""

from types import SimpleNamespace

import streamlit as st

import gui.sidebar as sd
import gui.visualisations as vis
import gui.widgets as wd
from gui import db
from gui.content import TEXT, WIDGETS
from utilities.columns import COLS, COLS_SQL

_state = st.session_state

cols = SimpleNamespace(**COLS)
cols_sql = SimpleNamespace(**COLS_SQL)
text = SimpleNamespace(**TEXT)
widgets = SimpleNamespace(**WIDGETS)


NULLS = "NULLS LAST"

st.set_page_config(
    layout="wide",
    page_title=text.APP_TITLE,
    page_icon=":receipt:",
    initial_sidebar_state="expanded",
)

# duckdb connection
con = db.get_con()

# get the shape file
gpd = db.get_shape_file()

# sidebar top
sd.top()

# widgets
wd.source_selector()
wd.payment_date_range_selector()
wd.is_removed_selector()
wd.is_spine_selector()

wd.init_nuts_state_vars()
wd.assign_state_nuts_keys(1)
if _state[wd.WIDGET_KEYS["IS_SPINE"]] is True:
    # manual and other match selectors
    wd.is_manual_match_selector()
    wd.is_other_match_selector()
    wd.apply_nuts_filter_selector()

    if _state[wd.WIDGET_KEYS["FILTER_NUTS"]] is True:
        # NUTS selectors
        wd.nuts_names_selector(1)
        if _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][1]]:
            wd.nuts_names_selector(2)

            if _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][2]]:
                wd.nuts_names_selector(3)
                if not _state[wd.WIDGET_KEYS["NUTS_NAMES"]["SELECTION"][3]]:
                    st.warning(text.ERROR_INCOMPLETE_SELECTIONS)
                    st.stop()
            else:
                st.warning(text.ERROR_INCOMPLETE_SELECTIONS)
                st.stop()
        else:
            st.warning(text.ERROR_INCOMPLETE_SELECTIONS)
            st.stop()
else:
    wd.reset_is_spine_state_vars()

where_clause, params = wd.build_where_clause_and_params()

vis.display_top_metrics(where_clause, params)

titles = widgets.VIEW_TABS["COMMON"].copy()
if _state[wd.WIDGET_KEYS["IS_SPINE"]] is True:
    titles += widgets.VIEW_TABS["SPINE"]
tabs_views = st.tabs(titles)

with tabs_views[0]:
    vis.display_raw_data(where_clause, params)

with tabs_views[1]:
    vis.display_suppliers(where_clause, params)

with tabs_views[2]:
    vis.display_timecourses(where_clause, params)

if _state[wd.WIDGET_KEYS["IS_SPINE"]] is not True:
    st.stop()

with tabs_views[3]:
    vis.display_geographical_distribution(where_clause, params)

with tabs_views[4]:
    vis.display_registry_distribution(where_clause, params)
