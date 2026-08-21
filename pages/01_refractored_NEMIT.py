import streamlit as st
import numpy as np
from utils.db_conn import get_database_engine
from utils.processing import has_stepsize_one
from utils.plotting import dynamic_groupby_bar_chart
from utils.UI import get_cached_regions, get_cached_gases
from services.pollution_services import (
    get_stations_by_regions, 
    get_common_years, 
    fetch_aggregated_pollution_data
)

st.set_page_config(layout="wide", page_title="Pollution Data Dashboard")
st.title('Environmental gas measurements')
st.sidebar.title('Time and gas filters')
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
selected_stations = st.multiselect("Please select Station/s:", sorted(stations), max_selections=3)

# ==============================================================================
# TEMPORAL METADATA
# ==============================================================================
common_years = get_common_years(conn, selected_stations)
if common_years:
    sorted_years = np.sort(common_years)
    if has_stepsize_one(sorted_years) and len(common_years) > 1:
        year_range = st.sidebar.slider("Year Range", min(common_years), max(common_years), (min(common_years), max(common_years)))
    else:
        year_range = st.sidebar.multiselect("Select Years", sorted_years)
else:
    year_range = st.sidebar.slider("Year Range", 2001, 2022, (2001, 2022))
    
# Month and Day Configuration
months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

month_map = {month: int(index)+1 for index, month in enumerate(months)}
days_map = {day: index+1 for index, day in enumerate(days)}

month_selection = st.sidebar.select_slider(
    'Month Range', options=months, value=("January", "December")
)
month_range = [month_map[month_selection[0]], month_map[month_selection[1]]]

day_selection = st.sidebar.select_slider(
    "Day Range", options=days, value=('Monday','Sunday')
)
day_range = [days_map[day_selection[0]], days_map[day_selection[1]]]

# ==============================================================================
# AGGREGATION FILTERS
# ==============================================================================
agg_method = st.sidebar.selectbox("Aggregation Method", ["Mean", "Median"])
timeframe = st.sidebar.selectbox("Timeframe", ["Year", "Month", "Day", "Hour"])

valid_gases = get_cached_gases(conn)
selected_gases = st.sidebar.multiselect("Select Air Pollutants", valid_gases, max_selections=2)

# ==============================================================================
# EXECUTION
# ==============================================================================
if st.button("Run Query", type="primary"):
    if not selected_stations or not selected_gases or not year_range:
        st.warning('Please ensure Station, Air Pollutant, and Year options are filled.')
        st.stop()
        
    with st.spinner("Aggregating temporal pollution data..."):
        grouped_df = fetch_aggregated_pollution_data(
            _conn=conn, 
            stations=selected_stations, 
            gases=selected_gases, 
            valid_gases=valid_gases,
            year_range=year_range, 
            month_range=month_range, 
            day_range=day_range, 
            timeframe=timeframe, 
            agg_method=agg_method
        )
        
        has_value = grouped_df is not None and not grouped_df.empty and grouped_df[selected_gases].notna().any().any()

        if has_value:
            st.success("Data Loaded Successfully")
            st.dataframe(grouped_df.head(10), use_container_width=True)
            #dynamic_groupby_bar_chart(grouped_df, selected_gases, timeframe)
        else:
            st.warning("No data found for the selected filter combination.")