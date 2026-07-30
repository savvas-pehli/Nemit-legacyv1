import pandas as pd
import streamlit as st
from utils.constants import VALID_TABLES
# ==============================================================================
# CONFIGURATION & WHITELISTS (Decoupling logic from the UI)
# ==============================================================================
DUCKDB_TIMEFRAME = {
    "Year": "EXTRACT(YEAR FROM {time_col})",
    "Month": "EXTRACT(MONTH FROM {time_col})",
    "Day": "EXTRACT(ISODOW FROM {time_col})",
    "Hour": "EXTRACT(HOUR FROM {time_col})"
}

@st.cache_data(ttl=86400, max_entries=5)
def get_port_metadata(_conn, table_alias: str) -> dict:
    """
    Dynamically fetches the time column, valid metrics, and chronological 
    boundaries for the target port table.
    """
    if table_alias not in VALID_TABLES:
        raise ValueError(f"Security Alert: Invalid table identifier '{table_alias}'")
        
    target_table = VALID_TABLES[table_alias]
    
    # 1. Identify the Time Column
    query_time = f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{target_table}' 
          AND data_type IN ('TIMESTAMP', 'DATETIME', 'DATE', 'TIMESTAMP WITH TIME ZONE');
    """
    time_col_df = _conn.execute(query_time).df()
    
    if time_col_df.empty:
        return {"time_col": None, "metrics": [], "min_year": None, "max_year": None}
        
    time_col = time_col_df['column_name'].iloc[0]
    
    # 2. Identify the Valid Measurement Metrics (Exclude IDs and Time columns)
    query_metrics = f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{target_table}' 
          AND data_type IN ('DOUBLE', 'FLOAT', 'INTEGER', 'NUMERIC', 'BIGINT')
          AND column_name != '{time_col}';
    """
    
    metrics_df = _conn.execute(query_metrics).df()
    metrics = metrics_df['column_name'].tolist()
    
    # 3. Establish Historical Bounds for Sliders
    query_bounds = f"""
        SELECT 
            MIN(EXTRACT(YEAR FROM "{time_col}")) AS min_y, 
            MAX(EXTRACT(YEAR FROM "{time_col}")) AS max_y 
        FROM thess_port_assesment.{target_table}
    """
    bounds_df = _conn.execute(query_bounds).df()
    min_y = int(bounds_df['min_y'].iloc[0]) if not pd.isna(bounds_df['min_y'].iloc[0]) else 2000
    max_y = int(bounds_df['max_y'].iloc[0]) if not pd.isna(bounds_df['max_y'].iloc[0]) else 2024
    
    return {
        "time_col": time_col, 
        "metrics": metrics, 
        "min_year": min_y, 
        "max_year": max_y
    }

@st.cache_data(ttl=3600, max_entries=10)
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
    """
    Executes the analytical query utilizing strict whitelisting for structural 
    components and TRUE parameter binding (?) for user values.
    """
    # 1. Structural Whitelisting (Cannot be parameterized by the DB)
    if table_alias not in VALID_TABLES:
        raise ValueError("Security Alert: Invalid table identifier")
    if timeframe not in DUCKDB_TIMEFRAME:
        raise ValueError("Security Alert: Invalid timeframe identifier")
        
    target_table = VALID_TABLES[table_alias]
    meta = get_port_metadata(_conn, table_alias)
    time_col = meta['time_col']
    
    if not time_col:
         raise ValueError(f"No temporal column found in {target_table}")

    time_expr = DUCKDB_TIMEFRAME[timeframe].format(time_col=f'"{time_col}"')
    sql_agg_func = 'AVG' if agg_type == 'Mean' else 'MEDIAN'
    
    # Safely building the SELECT clause using our verified measurement list
    agg_columns = ", ".join([f'{sql_agg_func}("{m}") AS "{m}"' for m in measurements])
    
    # 2. True Parameter Binding (The Fix)
    # Notice the '?' placeholders. The database treats these STRICTLY as literal values.
    query = f"""
        SELECT 
            {time_expr} AS time_bucket,
            {agg_columns}
        FROM thess_port_assesment.{target_table}
        WHERE EXTRACT(YEAR FROM "{time_col}") BETWEEN ? AND ?
          AND EXTRACT(MONTH FROM "{time_col}") BETWEEN ? AND ?
          AND EXTRACT(ISODOW FROM "{time_col}") BETWEEN ? AND ?
        GROUP BY time_bucket
        ORDER BY time_bucket ASC;
    """    
    
    # We pass the tuple of parameters directly to the execute function
    params = (
        year_range[0], year_range[1],
        month_range[0], month_range[1],
        day_range[0], day_range[1]
    )
    
    return _conn.execute(query, params).df()