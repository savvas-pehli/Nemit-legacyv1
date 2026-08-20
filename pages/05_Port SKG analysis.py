import streamlit as st
import pandas as pd
from utils.db_conn import get_database_engine
from services.port_services import get_port_metadata, fetch_aggregated_port_data
from utils.plotting import localized_dual_axis_chart
from utils.constants import MONTHS_LIST,MONTH_MAP,DAYS_LIST,DAYS_MAP, VALID_TABLES
st.set_page_config(page_title="Site Analytics", layout="wide")
st.title("Localized Environmental Analytics")
st.markdown("---")


conn = get_database_engine()
# ==============================================================================
# PRIMARY FILTERS (Triggers Schema Update)
# ==============================================================================
st.sidebar.markdown("### Analysis Parameters")

analysis_type = st.selectbox("Select Analysis Type:", options=list(VALID_TABLES.keys()))

try:
    meta = get_port_metadata(conn, analysis_type)
except Exception as e:
    st.error(f"Failed to retrieve schema: {e}")
    st.stop()

if not meta["time_col"]:
    st.error(f"Fatal Schema Error: No temporal column found for {analysis_type}.")
    st.stop()

# ==============================================================================
# DYNAMIC MEASUREMENT RETRIEVAL
# ==============================================================================
selected_metrics = st.multiselect(
    "Select Metrics to Analyze:", 
    options=meta["metrics"], 
    max_selections=2
)

# ==============================================================================
# TEMPORAL FILTERS
# ==============================================================================
min_y, max_y = meta["min_year"], meta["max_year"]

if min_y == max_y:
    st.sidebar.info(f"Data is locked to a single year: **{min_y}**")
    year_range = (min_y, min_y)
else:
    year_range = st.sidebar.slider("Select Year Range:", min_value=min_y, max_value=max_y, value=(min_y, max_y))

ui_month_range = st.sidebar.select_slider('Select Month Range', options=MONTHS_LIST, value=("January", "December"))
db_month_range = (MONTH_MAP[ui_month_range[0]], MONTH_MAP[ui_month_range[1]])

ui_day_range = st.sidebar.select_slider("Select Day of Week", options=DAYS_LIST, value=('Monday', 'Sunday'))
db_day_range = (DAYS_MAP[ui_day_range[0]], DAYS_MAP[ui_day_range[1]])

timeframe_options = ["Year", "Month", "Day", "Hour"]
timeframe = st.sidebar.selectbox("Timeframe Resolution:", timeframe_options)

agg_method = st.sidebar.selectbox("Aggregation Method:", ["Mean", "Median"])

# ==============================================================================
# CACHE CONTROL
# ==============================================================================
st.sidebar.markdown("### System Controls")
if st.sidebar.button("🔄 Force Refresh Data", type="primary"):
    st.cache_data.clear()
    st.sidebar.success("Cache wiped.")
st.sidebar.markdown("---")

# ==============================================================================
# AGGREGATION & EXECUTION
# ==============================================================================
if st.button("Generate Analysis", type="primary"):
    if not selected_metrics:
        st.warning("⚠️ You must select at least one metric.")
        st.stop()
        
    with st.spinner("Extracting insights from warehouse..."):
        try:
            df_result = fetch_aggregated_port_data(
                _conn=conn,
                agg_type=agg_method,
                table_alias=analysis_type,
                measurements=selected_metrics,
                timeframe=timeframe,
                year_range=year_range,
                month_range=db_month_range,
                day_range=db_day_range
            )
            
            if df_result.empty:
                st.warning("No data found for the selected parameters.")
                st.stop()
            
            # Map UI strings for display
            df_result.rename(columns={'time_bucket': timeframe}, inplace=True)
            
            if timeframe == "Day":
                # Isodow returns 1-7. Map it to text for visualization.
                isodow_map = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
                df_result[timeframe] = df_result[timeframe].map(isodow_map)
                df_result[timeframe] = pd.Categorical(df_result[timeframe], categories=DAYS_LIST, ordered=True)

            st.success("Data successfully processed.")
            localized_dual_axis_chart(df_result, selected_metrics, timeframe)
            
        except Exception as e:
            st.error(f"Execution Error: {e}")