import streamlit as st
import pandas as pd
from utils.db_conn import get_db_connection, fetch_query, quote
from utils.translation_helper import greek_to_latin
from data.sql_queries import CHOROPLETH_YEARLY_QUERY, GET_CHORO_GAS_COLUMNS_QUERY,CHOROPLETH_HOURLY_YEARLY_QUERY
from utils.processing import (
    hourly_df_with_polars,
    yearly_df_with_polars_from_raw
)
from utils.plotting import choropleth_mapbox
from utils.geo import load_geo_original_data  # to be added
import time
# Connect to DB
conn = get_db_connection()

st.title("GAS APP")
st.sidebar.title("Timeframe filters")

# Region selection
region = st.selectbox("Please select Region:", ["Attica", "Central Macedonia"])

# Timeframe logic mapping
timeframe_options = {
    "Yearly timeframe": {
        "frame": "year",
        "processor": lambda df, col, _: yearly_df_with_polars_from_raw(df, col)
    },
    "Last five years hours": {
        "frame": "Hour",
        "processor": lambda df, col, _: hourly_df_with_polars(df, col, "Last five years hours"),
    },
    "Certain year hours": {
        "frame": "Hour",
        "processor": lambda df, col, year: hourly_df_with_polars(df, col, "Certain year hours", year)
    }
}

# User selects timeframe
selected_timeframe = st.sidebar.selectbox("Please choose timeframe", list(timeframe_options.keys()))

# Column (air pollutant) selection
column_query = GET_CHORO_GAS_COLUMNS_QUERY
cols_result = fetch_query(conn, column_query)
columns = cols_result['COLUMN_NAME'].tolist() if cols_result is not None else []
selected_col = st.selectbox("Please select air pollutant", sorted(columns))
# Geo data


# Fetch raw data


query = CHOROPLETH_YEARLY_QUERY.format(
    air_pollutant=selected_col,
    region=quote(region)
)
gdf = fetch_query(conn, query)
#gdf['municipality'] = gdf['municipality'].apply(greek_to_latin)
municipality_ids=tuple(gdf['municipality'].apply(greek_to_latin).unique())
geodata = load_geo_original_data(region.capitalize(),municipality_ids)
# Year input for conditional timeframe
year_input = None
if selected_timeframe == "Certain year hours" and gdf is not None:
    query = CHOROPLETH_HOURLY_YEARLY_QUERY.format(
    air_pollutant=selected_col,
    region=quote(region)
)
    gdf = fetch_query(conn, query)
    year_list = sorted([int(year) for year in gdf['year'].unique()])
    year_input = st.sidebar.selectbox("Choose year", year_list)

if gdf is not None and (selected_timeframe != "Certain year hours" or year_input):
    query = CHOROPLETH_HOURLY_YEARLY_QUERY.format(
    air_pollutant=selected_col,
    region=quote(region)
)
    gdf = fetch_query(conn, query)
    gdf = timeframe_options[selected_timeframe]["processor"](gdf, selected_col, year_input)
    ani_frame = timeframe_options[selected_timeframe]["frame"]
    #gdf['municipality'] = gdf['municipality'].apply(greek_to_latin)

    if st.button("Show choropleth map"):
        gdf['municipality'] = gdf['municipality'].apply(greek_to_latin)
        choropleth_mapbox(gdf, geodata, selected_col, region, ani_frame)
else:
    st.warning("No data found or required inputs missing for the selected timeframe.")