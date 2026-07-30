import streamlit as st
from utils.db_conn import get_db_connection, fetch_cached_query
from utils.plotting import localized_dual_axis_chart 
from queries.sql_queries import PORT_AGGREGATION_QUERY
from utils.constants import PORT_TABLE_MAPPING, MONTHS_LIST, DAYS_LIST, MONTH_MAP, DAYS_MAP
from services.port_services import (
    get_cached_port_metadata, 
    get_cached_year_bounds, 
    get_cached_port_columns
)

st.set_page_config(page_title="Site Analytics", layout="wide")
st.title("Localized Environmental Analytics")

# 1. Connection Setup
conn = get_db_connection()

# --- CACHE CONTROL (The Manual Flush) ---
st.sidebar.markdown("### System Controls")
if st.sidebar.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.sidebar.success("Cache wiped. The next query will hit the database.")
st.sidebar.markdown("---")

st.sidebar.markdown("### Analysis Parameters")

analysis_type = st.selectbox("Select Analysis Type:", list(PORT_TABLE_MAPPING.keys()))
target_table = PORT_TABLE_MAPPING[analysis_type]

# 2. Cached Metadata Retrieval (Instantaneous)
time_col_name, time_col_type = get_cached_port_metadata(conn, target_table)

if not time_col_name:
    st.error(f"Fatal Schema Error: No DATE or TIMESTAMP column found in {target_table}.")
    st.stop()

year_bounds = get_cached_year_bounds(conn, target_table, time_col_name)
min_y, max_y = year_bounds["min_year"], year_bounds["max_year"]

if min_y == max_y:
    st.info(f"Data is locked to a single year: **{min_y}**")
    year_range = (min_y, min_y)
else:
    year_range = st.sidebar.slider("Select Year Range:", min_value=min_y, max_value=max_y, value=(min_y, max_y))

available_metrics = get_cached_port_columns(conn, target_table)
selected_metrics = st.multiselect("Select Metrics to Analyze:", available_metrics, max_selections=2)

# 3. Static Filters using Constants
month_range = st.sidebar.select_slider('Select Month Range', options=MONTHS_LIST, value=("January", "December"))
month_range_mapped = [MONTH_MAP[m] for m in month_range]

day_range = st.sidebar.select_slider("Select Day of Week", options=DAYS_LIST, value=('Monday', 'Sunday'))
day_range_mapped = [DAYS_MAP[d] for d in day_range]

has_hours = time_col_name.lower() in ["datetime", "timestamp"]
timeframe_options = ["Year", "Month", "Day", "Hour"] if has_hours else ["Year", "Month", "Day"]
timeframe = st.sidebar.selectbox("Timeframe", timeframe_options)

agg_method = st.sidebar.selectbox("Aggregation Method:", ["Mean", "Median"])

# 4. Query Execution
if st.button("Generate Analysis") and selected_metrics:
    sql_agg = "AVG" if agg_method == "Mean" else "MEDIAN"
    metric_aggs = ', '.join([f'{sql_agg}("{m}") AS "{m}"' for m in selected_metrics])
    
    sql_timeframe = {
        "Year": f"EXTRACT(YEAR FROM {time_col_name}) as Year",
        "Month": f"EXTRACT(MONTH FROM {time_col_name}) as Month",
        "Day": f"EXTRACT(ISODOW FROM {time_col_name}) as Day",
        "Hour": f"EXTRACT(HOUR FROM {time_col_name}) as Hour"
    }
    
    timeframe_expr = sql_timeframe[timeframe]
    
    data_query = PORT_AGGREGATION_QUERY.format(
        timeframe=timeframe_expr,
        timeframe_order=timeframe,
        metric_aggs=metric_aggs, 
        target_table=target_table,
        year_range=year_range,
        month_range=month_range_mapped,
        day_range=day_range_mapped
    )
    
    with st.spinner(f"Extracting {analysis_type} insights from warehouse..."):
        # HIT THE MEMORY-SAFE CACHE INSTEAD OF THE DB
        df = fetch_cached_query(conn, data_query)
    
    if df is not None and not df.empty:
        st.success("Data successfully retrieved.")
        localized_dual_axis_chart(df, selected_metrics, timeframe) 
    else:
        st.warning("No data found for the selected parameters.")
        
elif not selected_metrics:
    st.info("Please select at least one metric to begin.")