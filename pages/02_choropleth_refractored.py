import streamlit as st
from utils.db_conn import get_database_engine
from utils.translation_helper import greek_to_latin
from services.choroplet_services import (
    get_cached_choro_columns,
    get_cached_geometric_data,
    fetch_choropleth_data
)
from utils.processing import hourly_df_with_polars, yearly_df_with_polars_from_raw
from utils.plotting import choropleth_mapbox
from utils.geo import load_geo_original_data

st.set_page_config(layout="wide", page_title="Spatial Analytics")
st.title("Choropleth Spatial Analysis")

# ==============================================================================
# CACHE CONTROL
# ==============================================================================
st.sidebar.markdown("### System Controls")
if st.sidebar.button("🔄 Force Refresh Data", type="primary"):
    st.cache_data.clear()
    st.sidebar.success("Cache wiped. The next query will hit the database.")
st.sidebar.markdown("---")

conn = get_database_engine()

# ==============================================================================
# UI FILTERS & METADATA
# ==============================================================================
st.sidebar.title("Timeframe Filters")
region = st.selectbox("Please select Region:", ["Attica", "Central Macedonia"])

# Timeframe definitions
timeframe_options = {
    "Yearly timeframe": {"frame": "Year"},
    "Last five years hours": {"frame": "Hour"},
    "Certain year hours": {"frame": "Hour"}
} 
selected_timeframe = st.sidebar.selectbox("Please choose timeframe", list(timeframe_options.keys()))

valid_pollutants = get_cached_choro_columns(conn)
if not valid_pollutants:
    st.error("Fatal Error: Could not load pollutant schema.")
    st.stop()
    
selected_col = st.selectbox("Please select air pollutant", sorted(valid_pollutants))
# ==============================================================================
# DATA EXTRACTION
# ==============================================================================
# Fetch the exact required data once
raw_gdf = fetch_choropleth_data(conn, region, selected_col, selected_timeframe, valid_pollutants)

if raw_gdf is None or raw_gdf.empty:
    st.warning("No environmental data found for the selected parameters.")
    st.stop()

# ==============================================================================
# GEOMETRY EXTRACTION
# ==============================================================================
raw_geo_df = get_cached_geometric_data(conn, region, raw_gdf['municipality'].tolist())
if raw_geo_df is not None and not raw_geo_df.empty:
    geodata = load_geo_original_data(raw_geo_df)
else:
    st.error(f"⚠️ Spatial geometry data for {region} could not be retrieved.")
    st.stop()

# ==============================================================================
# DATA PROCESSING & RENDERING
# ==============================================================================
year_input = None
if selected_timeframe == "Certain year hours":
    # Ensure year column is treated correctly as integer for the slider
    year_list = sorted([int(year) for year in raw_gdf['Year'].dropna().unique()])
    if not year_list:
        st.warning("No valid years found for hourly analysis.")
        st.stop()
    year_input = st.sidebar.selectbox("Choose year", year_list)

if st.button("Generate Spatial Map", type="primary"):
    with st.spinner("Processing spatial polygons and aggregating metrics..."):
        try:
            # Route to the appropriate Polars processor
            if selected_timeframe == "Yearly timeframe":
                processed_df = yearly_df_with_polars_from_raw(raw_gdf, selected_col)
            elif selected_timeframe == "Last five years hours":
                processed_df = hourly_df_with_polars(raw_gdf, selected_col, selected_timeframe)
            else:
                processed_df = hourly_df_with_polars(raw_gdf, selected_col, selected_timeframe, year_input)
            
            if processed_df.empty:
                st.warning("Processing resulted in an empty dataset.")
                st.stop()
                
            # Apply translation strictly on the finalized dataframe
            processed_df['municipality'] = processed_df['municipality'].apply(greek_to_latin)
            ani_frame = timeframe_options[selected_timeframe]["frame"]
            choropleth_mapbox(processed_df, geodata, selected_col, region, ani_frame)
            
        except Exception as e:
            st.error(f"Processing Error: {e}")