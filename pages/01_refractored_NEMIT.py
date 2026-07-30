import streamlit as st
import os
import sys
import numpy as np
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from utils.db_conn import get_db_connection, fetch_query, format_in_clause
from utils.processing import has_stepsize_one
from queries.sql_queries import (
    GET_STATIONS_BY_REGIONS_QUERY,
    GET_COMMON_YEARS_FOR_STATIONS,GET_ALL_STATIONS_QUERY,
    GET_AGGREGATTED_DATA,
)
from utils.plotting import dynamic_groupby_bar_chart
from utils.UI import get_cached_regions, get_cached_gases

st.set_page_config(layout="wide", page_title="Pollution Data Dashboard")
st.sidebar.title('Time and gas filters')
conn = get_db_connection()

# Region and Station Selection
regions=get_cached_regions(conn)
if regions is not None and len(regions) > 0:
    # 3. Use the EXACT casing that exists in your database
    selected_regions = st.multiselect("Please select Region/s:", regions)
else:
    st.error("⚠️ Connection lost or no regions found. Please refresh the page.")
    st.stop() # Halts the script safely instead of throwing a red error screen


    
if selected_regions:
    region_clause = format_in_clause(selected_regions)
    station_query = GET_STATIONS_BY_REGIONS_QUERY.format(regions=region_clause)
    stations = fetch_query(conn, station_query)['station'].tolist()
else:
    stations = fetch_query(conn, GET_ALL_STATIONS_QUERY)['station'].tolist()
stations=[station.capitalize() for station in stations]
selected_stations = st.multiselect("Please select Station/s:", sorted(stations), max_selections=3)



# Common Year Selection
if selected_stations:
    station_clause = format_in_clause([station.upper() for station in selected_stations])
    year_query = GET_COMMON_YEARS_FOR_STATIONS.format(
        stations=station_clause,
        station_count=len(selected_stations)
    )
    years_df = fetch_query(conn, year_query)
    common_years = years_df['Year'].tolist() if years_df is not None else []
else:
    common_years = []
    

if common_years:
    if has_stepsize_one(np.sort(common_years)) and len(common_years) > 1:
        year_range = st.sidebar.slider("Year Range", min(common_years), max(common_years), (min(common_years), max(common_years)))
    else:
        year_range = st.sidebar.multiselect("Select Years", common_years.sort())
else:
    year_range = st.sidebar.slider("Year Range", 2001, 2022, (2001, 2022))
    
# Month and Day Range
months = list(range(1, 13))
days_of_week = list(range(0, 7))
months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
        ]
        
days =['Monday','Tuesday','Wednesday','Thursday','Firday','Saturday','Sunday']
month_map = {month: int(index)+1  for index, month in enumerate(months)}
days_map={day: index for index, day in enumerate(days)}
month_range = st.sidebar.select_slider(label=' ',options=months,value=("January", "December"),
                                help='Here you can set the range \n of months you would like to apply to the data')
month_range=[month_map[month] for month in month_range]
day_range = st.sidebar.select_slider(" ", options=days,value=('Monday','Sunday'),
                                help='Select days range (for just one day get both sides of slider at the day you want)')
day_range=[days_map[day] for day in day_range]
# Timeframe and Aggregation
agg_method = st.sidebar.selectbox("Aggregation Method", ["Mean", "Median"])
timeframe = st.sidebar.selectbox("Timeframe", ["Year", "Month", "Day", "Hour"])

# Gas Pollutant Selection
gas_columns = get_cached_gases(conn)
selected_gases = st.sidebar.multiselect("Select Air Pollutants", gas_columns, max_selections=2)


# Query Construction and Execution
if st.button("Run Query") and selected_stations and selected_gases and year_range:
    if isinstance(year_range, tuple):
        year_condition = f"Year BETWEEN {year_range[0]} AND {year_range[1]}"
    else:
        year_condition = f"Year IN ({', '.join(map(str, year_range))})"

    
    sql_timeframe = {
        "Year": "EXTRACT(YEAR FROM record_datetime)",
        "Month": "EXTRACT(MONTH FROM record_datetime)",
        "Day": "EXTRACT(ISODOW FROM record_datetime)",
        "Hour": "EXTRACT(HOUR FROM record_datetime)"
    }
    
    sql_agg = {
        "Mean": "AVG",
        "Median": "MEDIAN"
    }    
    
    timeframe_expr = sql_timeframe[timeframe]
    gas_aggs = ', '.join([f'{sql_agg[agg_method]}("{gas}") AS "{gas}"' for gas in selected_gases])
    
    
    data_query = GET_AGGREGATTED_DATA.format(
        timeframe=timeframe_expr,
        gas=gas_aggs,
        stations=station_clause,
        year_condition=year_condition,
        month_start=month_range[0],
        month_end=month_range[1],
        dow_start=day_range[0],
        dow_end=day_range[1]
    )
    grouped_df = fetch_query(conn, data_query)
    if isinstance(selected_gases, str):
        selected_gases = [selected_gases]
# Check if any of the selected columns have at least one non-null value
    has_value = grouped_df is not None and not grouped_df.empty and grouped_df[selected_gases].notna().any().any()

    
    if has_value:
        # Plotting
        st.write(grouped_df.head())
        st.success("Data Loaded Successfully")
        dynamic_groupby_bar_chart(grouped_df, selected_gases, timeframe)
    else:
        st.warning("No data found for the selected filter combination.")
else:
    st.warning(r'Please be sure that you have filled Station, Air Pollutant and Year options before press the Run Query button')