import pandas as pd
import streamlit as st
from utils.db_conn import fetch_query
from utils.constants import VALID_TABLES
from queries.postegre_queries import (
    PORT_TIME_COLUMN_QUERY,
    PORT_METRICS_COLUMN_QUERY,
    PORT_TIME_BOUNDARIES_QUERY,
    PORT_AGGREGATION_QUERY
)
# ==============================================================================
# CONFIGURATION & WHITELISTS (Decoupling logic from the UI)
# ==============================================================================
PG_TIMEFRAME = {
    "Year": 'EXTRACT(YEAR FROM "{time_col}")',
    "Month": 'EXTRACT(MONTH FROM "{time_col}")',
    "Day": 'EXTRACT(ISODOW FROM "{time_col}")',
    "Hour": 'EXTRACT(HOUR FROM "{time_col}")'
}



@st.cache_data(ttl=86400, max_entries=5, show_spinner=False)
def get_port_metadata(_conn, table_alias: str) -> dict:
    """Dynamically fetches safe table metrics using strict parameterization."""
    if table_alias not in VALID_TABLES:
        raise ValueError(f"Security Alert: Invalid table identifier '{table_alias}'")
        
    target_table = VALID_TABLES[table_alias]
    
    # 1. Identify Time Column
    time_col_df = fetch_query(_conn, PORT_TIME_COLUMN_QUERY, params={"target_table": target_table})
    if time_col_df is None or time_col_df.empty:
        return {"time_col": None, "metrics": [], "min_year": None, "max_year": None}
        
    time_col = time_col_df['column_name'].iloc[0]
    
    # 2. Identify Metrics
    metrics_df = fetch_query(_conn, PORT_METRICS_COLUMN_QUERY, params={"target_table": target_table, "time_col": time_col})
    metrics = metrics_df['column_name'].tolist() if metrics_df is not None else []
    
    # 3. Establish Historical Bounds
    query_bounds = PORT_TIME_BOUNDARIES_QUERY.format(time_col=time_col, target_table=target_table)
    bounds_df = fetch_query(_conn, query_bounds)
    
    min_y = int(bounds_df['min_y'].iloc[0]) if bounds_df is not None and not pd.isna(bounds_df['min_y'].iloc[0]) else 2000
    max_y = int(bounds_df['max_y'].iloc[0]) if bounds_df is not None and not pd.isna(bounds_df['max_y'].iloc[0]) else 2024
    
    return {
        "time_col": time_col, 
        "metrics": metrics, 
        "min_year": min_y, 
        "max_year": max_y
    }

@st.cache_data(ttl=3600, max_entries=10, show_spinner=False)
def fetch_aggregated_port_data(
    _conn,
    agg_type: str,
    table_alias: str,
    measurements: list,
    timeframe: str,
    year_range: tuple,
    month_range: tuple,
    day_range: tuple
) -> pd.DataFrame:
    """Executes the analytical query using dictionary parameter mapping."""
    if table_alias not in VALID_TABLES:
        raise ValueError("Security Alert: Invalid table identifier")
    if timeframe not in PG_TIMEFRAME:
        raise ValueError("Security Alert: Invalid timeframe identifier")
        
    target_table = VALID_TABLES[table_alias]
    meta = get_port_metadata(_conn, table_alias)
    time_col = meta['time_col']
    
    if not time_col:
         raise ValueError(f"No temporal column found in {target_table}")

    # Inject the actual column name into the extraction template
    time_expr = PG_TIMEFRAME[timeframe].format(time_col=time_col)
    
    # Map the correct PostgreSQL aggregation function
    if agg_type == 'Mean':
        agg_columns = ", ".join([f'AVG("{m}") AS "{m}"' for m in measurements])
    elif agg_type == 'Median':
        agg_columns = ", ".join([f'PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY "{m}") AS "{m}"' for m in measurements])
    else:
        raise ValueError("Security Alert: Invalid aggregation method")
    
    # Inject structural elements
    query = PORT_AGGREGATION_QUERY.format(
        time_expr=time_expr,
        agg_columns=agg_columns,
        target_table=target_table,
        time_col=time_col
    )    
    
    # Strictly map dictionary parameters
    params = {
        "start_year": year_range[0], "end_year": year_range[1],
        "start_month": month_range[0], "end_month": month_range[1],
        "start_day": day_range[0], "end_day": day_range[1]
    }
    
    return fetch_query(_conn, query, params=params)