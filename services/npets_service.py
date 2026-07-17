import pandas as pd
from sqlalchemy import text
import streamlit as st
from utils.db_conn import format_in_clause
# ==============================================================================
# CONFIGURATION & WHITELISTS (Decoupling logic from the UI)
# ==============================================================================
VALID_TOOLS = {
    "ELPI": "elpi",
    "OPS": "ops",
    "METADATA": "metadata"
}

# MySQL-compliant time extraction
DUCKDB_TIMEFRAME = {
    "Day": "(EXTRACT(ISODOW FROM f.Datetime) - 1)", # Maps 1-7 (Mon-Sun) down to 0-6 to match UI map
    "Hour": "EXTRACT(HOUR FROM f.Datetime)"
}

def get_npets_schema(conn, tool_name: str) -> list:
    """
    Interrogates the MySQL Information Schema to dynamically return 
    measurement columns for a specific tool.
    """
    if tool_name not in VALID_TOOLS:
        raise ValueError(f"Security Alert: Invalid tool '{tool_name}'")
        
    target_table = VALID_TOOLS[tool_name]
    
    # We query npets_tables and strictly exclude mechanical keys
    query = f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{target_table}' 
          AND column_name NOT IN ('experiment_id', 'Datetime', 'Time', 'Date');
    """
    df = conn.execute(query).df()    
    return df['column_name'].tolist()

@st.cache_data(ttl=3600)
def fetch_aggregated_npets_data(
    _conn, 
    tool_name: str, 
    places: list, 
    seasons: list, 
    measurements: list, 
    timeframe: str
) -> pd.DataFrame:
    """
    Executes the analytical JOIN query utilizing bound parameters for security.
    """
    # 1. State Validation
    if tool_name not in VALID_TOOLS:
        raise ValueError("Security Alert: Invalid tool identifier")
    if timeframe not in DUCKDB_TIMEFRAME:
        raise ValueError("Security Alert: Invalid timeframe identifier")
        
    target_table = VALID_TOOLS[tool_name]
    time_expr = DUCKDB_TIMEFRAME[timeframe]
    
    # 2. Dynamic Math Application (Hardcoded to Mean/AVG for now)
    agg_columns = ", ".join([f'AVG(f."{m}") AS "{m}"' for m in measurements])
    
    # 3. Dynamic Parameter Binding Arrays
    places_in = format_in_clause(places)
    seasons_in = format_in_clause(seasons)
    

    
    # 4. Construct and Execute the Star Schema Query
    query = f"""
        SELECT 
             d.location,
             d.season,
            {time_expr} AS time_bucket,
            {agg_columns}
        FROM npets_tables.{target_table} f
        JOIN npets_tables.dim_experiment d ON f.experiment_id = d.experiment_id
        WHERE d.location IN {places_in}
          AND d.season IN {seasons_in.upper()}
        GROUP BY ALL
        ORDER BY time_bucket ASC;
    """    
    df =_conn.execute(query).df()
    return df


@st.cache_data(ttl=3600)
def fetch_temporal_metadata(
    _conn, 
    tool_name: str, 
    places: list, 
    seasons: list
) -> dict:
    """
    Executes a high-speed DISTINCT scan to determine the exact temporal footprint 
    (Years and Months) of the sliced data before mathematical aggregation occurs.
    """
    if tool_name not in VALID_TOOLS:
        raise ValueError("Security Alert: Invalid tool identifier")
        
    target_table = VALID_TOOLS[tool_name]
    
    places_in = format_in_clause(places)
    seasons_in = format_in_clause(seasons)
    
    
    # We query only for the distinct chronological components
    query = f"""
        SELECT DISTINCT 
            EXTRACT(YEAR FROM f.Datetime) AS data_year,
            EXTRACT(MONTH FROM f.Datetime) AS data_month
        FROM npets_tables.{target_table} f
        JOIN npets_tables.dim_experiment d ON f.experiment_id = d.experiment_id
        WHERE d.location IN {places_in}
          AND d.season IN {seasons_in.upper()}
        ORDER BY data_year ASC, data_month ASC;
    """
    df = _conn.execute(query).df()
    df.dropna(subset=['data_year', 'data_month'], how='all', inplace=True)
    
    if df.empty:
        return {"years": [], "months": []}
    
    return {
        "years": df['data_year'].astype(int).unique().tolist(),
        "months": df['data_month'].astype(int).unique().tolist()
    }