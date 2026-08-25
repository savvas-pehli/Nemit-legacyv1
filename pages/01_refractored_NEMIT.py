import numpy as np
import streamlit as st
from services.pollution_services import (
    fetch_aggregated_pollution_data,
    get_common_years,
    get_stations_by_regions,
)
from utils.constants import DAYS_LIST, DAYS_MAP, MONTH_MAP, MONTHS_LIST
from utils.db_conn import get_database_engine
from utils.plotting import dynamic_groupby_bar_chart
from utils.processing import has_stepsize_one
from utils.UI import get_cached_gases, get_cached_regions

st.set_page_config(layout="wide", page_title="Pollution Data Dashboard")
st.title("Environmental gas measurements")
st.sidebar.title("Time and gas filters")
st.sidebar.markdown("### System Controls")
if st.sidebar.button("🔄 Force Refresh Data", type="primary"):
    st.cache_data.clear()
    st.sidebar.success("Cache wiped. The next query will hit the database.")
st.sidebar.markdown("---")

conn = get_database_engine()

# ==============================================================================
# GEOGRAPHY METADATA
# ==============================================================================
regions = get_cached_regions(conn)
if not regions:
    st.error("⚠️ Connection lost or no regions found. Please refresh the page.")
    st.stop()

selected_regions = st.multiselect("Please select Region/s:", regions)
stations = get_stations_by_regions(conn, selected_regions)
selected_stations = st.multiselect(
    "Please select Station/s:", sorted(stations), max_selections=3
)

# ==============================================================================
# TEMPORAL METADATA
# ==============================================================================
common_years = get_common_years(conn, selected_stations)
if common_years:
    sorted_years = np.sort(common_years)
    if has_stepsize_one(sorted_years) and len(common_years) > 1:
        year_range = st.sidebar.slider(
            "Year Range",
            min(common_years),
            max(common_years),
            (min(common_years), max(common_years)),
        )
    else:
        year_range = st.sidebar.multiselect("Select Years", sorted_years)
else:
    year_range = st.sidebar.slider("Year Range", 2001, 2022, (2001, 2022))

# Month and Day Configuration
month_selection = st.sidebar.select_slider(
    "Month Range", options=MONTHS_LIST, value=("January", "December")
)
month_range = [MONTH_MAP[month_selection[0]], MONTH_MAP[month_selection[1]]]

day_selection = st.sidebar.select_slider(
    "Day Range", options=DAYS_LIST, value=("Monday", "Sunday")
)
day_range = [DAYS_MAP[day_selection[0]], DAYS_MAP[day_selection[1]]]

# ==============================================================================
# AGGREGATION FILTERS
# ==============================================================================
agg_method = st.sidebar.selectbox("Aggregation Method", ["Mean", "Median"])
timeframe = st.sidebar.selectbox("Timeframe", ["Year", "Month", "Day", "Hour"])

valid_gases = get_cached_gases(conn)
selected_gases = st.sidebar.multiselect(
    "Select Air Pollutants", valid_gases, max_selections=2
)

# ==============================================================================
# EXECUTION
# ==============================================================================
if st.button("Generate Analysis", type="primary"):
    if not selected_stations or not selected_gases or not year_range:
        st.warning("Please ensure Station, Air Pollutant, and Year options are filled.")
        st.stop()

    with st.spinner("Extracting insights from warehouse..."):
        try:
            grouped_df = fetch_aggregated_pollution_data(
                _conn=conn,
                stations=selected_stations,
                gases=selected_gases,
                valid_gases=valid_gases,
                year_range=year_range,
                month_range=month_range,
                day_range=day_range,
                timeframe=timeframe,
                agg_method=agg_method,
            )

            has_value = (
                grouped_df is not None
                and not grouped_df.empty
                and grouped_df[selected_gases].notna().any().any()
            )

            if has_value:
                st.success("Data successfully processed.")
                dynamic_groupby_bar_chart(grouped_df, selected_gases, timeframe)
            else:
                st.warning("No data found for the selected filter combination.")

        except Exception as e:
            st.error(f"Execution Error: {e}")
