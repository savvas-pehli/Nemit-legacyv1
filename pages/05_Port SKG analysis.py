import streamlit as st
import pandas as pd
from utils.db_conn import get_db_connection, fetch_query
from utils.plotting import localized_dual_axis_chart 
from queries.sql_queries import PORT_COLUMNS_QUERY,PORT_AGGREGATION_QUERY
from utils.UI import get_port_table_columns, get_port_time_column_metadata,get_dynamic_year_bounds


st.set_page_config(page_title="Site Analytics", layout="wide")

st.title("Localized Environmental Analytics")
conn = get_db_connection()


table_mapping = {
    "Atmospheric Gases": 'port_thessaloniki_gases',
    "Particles": 'port_thessaloniki_particles',
    "Acoustic/Sound Levels": 'port_thessaloniki_noise',
    "Water Quality": 'port_thessaloniki_water_quality'
}


st.sidebar.markdown("### Analysis Parameters")

# Core Table Routing
analysis_type = st.selectbox("Select Analysis Type:", list(table_mapping.keys()))
target_table = table_mapping[analysis_type]
time_col_name, time_col_type = get_port_time_column_metadata(conn, target_table)

if not time_col_name:
        st.error(f"Fatal Schema Error: No DATE or TIMESTAMP column found in {target_table}.")
        st.stop()

# Get dynamic year bounds
year_bounds = get_dynamic_year_bounds(conn, target_table, time_col_name)
min_y = year_bounds["min_year"]
max_y = year_bounds["max_year"]

if min_y == max_y:
        # Prevent slider crash if data only spans exactly one year
        st.info(f"Data is locked to a single year: **{min_y}**")
        year_range = (min_y, min_y)
else:
        # Dynamic slider based on actual database contents
        year_range = st.sidebar.slider(
            "Select Year Range:", 
            min_value=min_y, 
            max_value=max_y, 
            value=(min_y, max_y)
        )
# Dynamic Column Fetching (Hits cache after first load)
available_metrics = get_port_table_columns(conn, table_name=target_table)
selected_metrics = st.multiselect("Select Metrics to Analyze:", available_metrics, max_selections=2)

# Time Filters
month_range = st.sidebar.slider("Select Month Range:", min_value=1, max_value=12, value=(1, 12))
day_range = st.sidebar.slider("Select Day of Week (1=Mon, 7=Sun):", min_value=1, max_value=7, value=(1, 7))

# 3. Dynamic UI: Only show the Hour slider if the data type supports it
has_hours = time_col_name in ["Datetime", "timestamp"]
    
if has_hours:
    timeframe = st.sidebar.selectbox("Timeframe", ["Year", "Month", "Day", "Hour"])
else:
    timeframe = st.sidebar.selectbox("Timeframe", ["Year", "Month", "Day"])
        
# Aggregation Strategy
agg_method = st.sidebar.selectbox("Aggregation Method:", ["Mean", "Median"])
#==============================================================================
# 3. QUERY EXECUTION (MotherDuck Pushdown)
# ==============================================================================

if st.button("Generate Analysis") and selected_metrics:
    # Map UI selection to SQL function
    sql_agg = "AVG" if agg_method == "Mean" else "MEDIAN"
    
    # Build dynamic select string (e.g., 'AVG("NO2") AS "NO2", AVG("O3") AS "O3"')
    # ALWAYS use double quotes to prevent WebGL/Plotly string-parsing crashes
    metric_aggs = ', '.join([f'{sql_agg}("{m}") AS "{m}"' for m in selected_metrics])
    
    sql_timeframe = {
        "Year": f"EXTRACT(YEAR FROM {time_col_name}) as Year",
        "Month": f"EXTRACT(MONTH FROM {time_col_name}) as Month",
        "Day": f"EXTRACT(ISODOW FROM {time_col_name}) as Day",
        "Hour": f"EXTRACT(HOUR FROM {time_col_name}) as Hour"
    }
    
    
    timeframe_expr = sql_timeframe[timeframe]
    # The Optimized Query
    data_query = PORT_AGGREGATION_QUERY.format(
        timeframe=timeframe_expr,
        timeframe_order=timeframe,
        metric_aggs=metric_aggs, 
        target_table=target_table,
        year_range=year_range,
        month_range=month_range,
        day_range=day_range
    )
    with st.spinner(f"Extracting {analysis_type} insights from warehouse..."):
        df = fetch_query(conn, data_query)
    
    # ==============================================================================
    # 4. RENDERING
    # ==============================================================================
    if df is not None and not df.empty:
        st.success("Data successfully processed by MotherDuck.")
        
        # Pass the microscopic, pre-aggregated dataframe directly to your plotting utility
        # Modify this line to point to your specific histogram function
        localized_dual_axis_chart(df, selected_metrics,timeframe) 

    else:
        st.warning("No data found for the selected parameters.")
        
elif not selected_metrics:
    st.info(" Please select at least one metric to begin.")