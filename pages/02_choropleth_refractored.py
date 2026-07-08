import streamlit as st
from utils.db_conn import get_db_connection, fetch_query, quote
from utils.translation_helper import greek_to_latin
from queries.sql_queries import CHOROPLETH_YEARLY_QUERY, GET_CHORO_GAS_COLUMNS_QUERY,CHOROPLETH_HOURLY_YEARLY_QUERY,GEOMETRIC_DATA_LOAD
from utils.processing import (
    hourly_df_with_polars,
    yearly_df_with_polars_from_raw
)
from utils.plotting import choropleth_mapbox
from utils.geo import load_geo_original_data  # to be added
# Connect to DB
conn = get_db_connection()

st.title("GAS APP")
st.sidebar.title("Timeframe filters")

# Region selection
region = st.selectbox("Please select Region:", ["Attica", "Central Macedonia"])

# Timeframe logic mapping
timeframe_options = {
    "Yearly timeframe": {
        "frame": "Year",
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
columns = cols_result['column_name'].tolist() if cols_result is not None else []
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
region_to_query = region.replace(" ", "_")
geo_query=GEOMETRIC_DATA_LOAD.format(table=region_to_query,
                                     municipalities=', '.join([f"'{id}'" for id in municipality_ids]))
raw_geo_df=fetch_query(conn,geo_query)
#geodata = load_geo_original_data(region.capitalize(),municipality_ids)

if raw_geo_df is not None and not raw_geo_df.empty:
    # 3. Inject the data into the pure utility function
    geodata = load_geo_original_data(raw_geo_df)
else:
    st.error(f"⚠️ Spatial data for {region} could not be retrieved from the database.")
    st.stop()
# Year input for conditional timeframe
year_input = None
if selected_timeframe == "Certain year hours" and gdf is not None:
    query = CHOROPLETH_HOURLY_YEARLY_QUERY.format(
    air_pollutant=selected_col,
    region=quote(region)
)
    st.write(query)
    gdf = fetch_query(conn, query)
    year_list = sorted([int(year) for year in gdf['Year'].unique()])
    year_input = st.sidebar.selectbox("Choose year", year_list)

if gdf is not None and (selected_timeframe != "Certain year hours" or year_input):
    query = CHOROPLETH_HOURLY_YEARLY_QUERY.format(
    air_pollutant=selected_col,
    region=quote(region)
)
    gdf = fetch_query(conn, query)
    gdf = timeframe_options[selected_timeframe]["processor"](gdf, selected_col, year_input)
    ani_frame = timeframe_options[selected_timeframe]["frame"]
    gdf['municipality'] = gdf['municipality'].apply(greek_to_latin)

    if st.button("Show choropleth map"):
        gdf['municipality'] = gdf['municipality'].apply(greek_to_latin)
        choropleth_mapbox(gdf, geodata, selected_col, region, ani_frame)
else:
    st.warning("No data found or required inputs missing for the selected timeframe.")