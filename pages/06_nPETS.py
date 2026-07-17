import streamlit as st
from utils.db_conn import get_db_connection
from services.npets_service import get_npets_schema, fetch_aggregated_npets_data
from utils.plotting import plot_particle_distribution
import pandas as pd
import calendar
from services.npets_service import fetch_temporal_metadata
st.set_page_config(layout="wide", page_title="nPETS Particle Analysis")

st.markdown("## ⚙️ nPETS Particle Distribution Analysis")
st.markdown("---")

# Constants
TOOLS = ["ELPI", "OPS", "METADATA"]
PLACES = ["SKG Airport", "SKG Port", "SKG CERTH", "SKG AUTH Main Road"]
SEASONS = ["Warm", "Cold"]
TIMEFRAMES = ["Day", "Hour"]
PLACE_MAPPING = {"SKG Airport": 'Airport', "SKG Port": 'Port', "SKG CERTH": 'Background', "SKG AUTH Main Road": 'Road'}

# Initialize Database Connection
conn = get_db_connection()

# ==============================================================================
# 1. PRIMARY FILTERS (Triggers Schema Update)
# ==============================================================================
st.markdown("### Base Filters")
col1, col2, col3 = st.columns(3)

selected_tool = st.sidebar.selectbox("Select Tool Engine:", options=TOOLS)
selected_places = st.sidebar.multiselect("Select Place (Max 2):", options=PLACES, default=[PLACES[0]], max_selections=2)
selected_seasons = st.sidebar.multiselect("Select Season(s):", options=SEASONS, default=SEASONS)

if not selected_places or not selected_seasons:
    st.warning("⚠️ Please select at least one Place and one Season.")
    st.stop()

# ==============================================================================
# 2. DYNAMIC MEASUREMENT RETRIEVAL
# ==============================================================================
try:
    available_columns = get_npets_schema(conn, selected_tool)
except Exception as e:
    st.error(f"Failed to retrieve schema: {e}")
    st.stop()

st.markdown("### Measurement Selection")
if available_columns:
    selected_measurements = st.multiselect(
        "Select Particle Bins to Analyze:", 
        options=available_columns,
        default=available_columns[:2] if len(available_columns) >= 2 else available_columns,
        max_selections=2
    )
else:
    st.error(f"No measurement columns found for {selected_tool}.")
    st.stop()

if not selected_measurements:
    st.warning("⚠️ You must select at least one measurement bin.")
    st.stop()

# ==============================================================================
# 3. AGGREGATION & EXECUTION
# ==============================================================================
st.markdown("### Time Aggregation")
selected_timeframe = st.radio("Select Time Resolution:", options=TIMEFRAMES, horizontal=True)

# Map UI strings to database strings
db_places = [PLACE_MAPPING[p] for p in selected_places]

# Execution Button
if st.button("Execute Analysis", type="primary"):
    with st.spinner("Executing analytical join..."):
        try:
            df_result = fetch_aggregated_npets_data(
                _conn=conn,
                tool_name=selected_tool,
                places=db_places,
                seasons=selected_seasons,
                measurements=selected_measurements,
                timeframe=selected_timeframe
            )
            if df_result.empty:
                st.warning("No data found for the selected parameters.")
                st.stop()
            
            meta = fetch_temporal_metadata(
                _conn=conn,
                tool_name=selected_tool,
                places=db_places,
                seasons=selected_seasons
            )
            
            REVERSE_PLACE_MAPPING = {v: k for k, v in PLACE_MAPPING.items()}
            df_result['location'] = df_result['location'].map(REVERSE_PLACE_MAPPING)
            
            if selected_timeframe == "Day":
                day_map = {
                    0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 
                    3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
                }
                df_result['time_bucket'] = df_result['time_bucket'].map(day_map)
                # Force Plotly to respect chronological order, not alphabetical order
                df_result['time_bucket'] = pd.Categorical(
                    df_result['time_bucket'], 
                    categories=list(day_map.values()), 
                    ordered=True
                )
            
            # 3. Rename the vague 'time_bucket' to the actual timeframe selected
            df_result.rename(columns={'time_bucket': selected_timeframe}, inplace=True)
            df_result.dropna(how='all', inplace=True)
            years_str = ", ".join(map(str, meta["years"]))
            months_str = ", ".join([calendar.month_abbr[m] for m in meta["months"]])
            
            # Display the Contextual Banner
            st.success(f"📊 **Contextual Temporal Footprint:** The graph below displays diurnal/weekly averages strictly derived from data recorded during the **Years {years_str}** across the **Months {months_str}**.")
            #st.dataframe(df_result, width='stretch')
            fig = plot_particle_distribution(df_result, selected_measurements, selected_timeframe)
            if fig:
                st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Execution Error: {e}")