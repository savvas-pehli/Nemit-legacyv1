import pandas as pd
from sqlalchemy import text
import streamlit as st

# ==============================================================================
# CONFIGURATION & WHITELISTS (Decoupling logic from the UI)
# ==============================================================================
VALID_TOOLS = {
    "ELPI": "elpi",
    "OPS": "ops",
    "METADATA": "metadata"
}

# MySQL-compliant time extraction
MYSQL_TIMEFRAME = {
    "Day": "WEEKDAY(f.Datetime)",
    "Hour": "HOUR(f.Datetime)"
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
    query = text("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = :table_name 
          AND TABLE_SCHEMA = 'npets_tables' 
          AND COLUMN_NAME NOT IN ('experiment_id', 'Datetime', 'Time', 'Date');
    """)
    
    df = pd.read_sql(query, conn.engine, params={"table_name": target_table})
    return df['COLUMN_NAME'].tolist()

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
    if timeframe not in MYSQL_TIMEFRAME:
        raise ValueError("Security Alert: Invalid timeframe identifier")
        
    target_table = VALID_TOOLS[tool_name]
    time_expr = MYSQL_TIMEFRAME[timeframe]
    
    # 2. Dynamic Math Application (Hardcoded to Mean/AVG for now)
    agg_columns = ", ".join([f"AVG(f.`{m}`) AS `{m}`" for m in measurements])
    
    # 3. Dynamic Parameter Binding Arrays
    place_binds = [f":place_{i}" for i in range(len(places))]
    season_binds = [f":season_{i}" for i in range(len(seasons))]
    
    params = {}
    for i, p in enumerate(places): params[f"place_{i}"] = p
    for i, s in enumerate(seasons): params[f"season_{i}"] = s
    
    # 4. Construct and Execute the Star Schema Query
    query = text(f"""
        SELECT 
             d.location,
             d.season,
            {time_expr} AS time_bucket,
            {agg_columns}
        FROM npets_tables.{target_table} f
        JOIN npets_tables.dim_experiment d ON f.experiment_id = d.experiment_id
        WHERE d.location IN ({", ".join(place_binds)})
          AND d.season IN ({", ".join(season_binds)})
        GROUP BY d.location, d.season, time_bucket
        ORDER BY time_bucket ASC;
    """)
    return pd.read_sql(query, _conn.engine, params=params)


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
    
    place_binds = [f":place_{i}" for i in range(len(places))]
    season_binds = [f":season_{i}" for i in range(len(seasons))]
    
    params = {}
    for i, p in enumerate(places): params[f"place_{i}"] = p
    for i, s in enumerate(seasons): params[f"season_{i}"] = s
    
    # We query only for the distinct chronological components
    query = text(f"""
        SELECT DISTINCT 
            EXTRACT(YEAR FROM f.Datetime) AS data_year,
            EXTRACT(MONTH FROM f.Datetime) AS data_month
        FROM npets_tables.{target_table} f
        JOIN npets_tables.dim_experiment d ON f.experiment_id = d.experiment_id
        WHERE d.location IN ({", ".join(place_binds)})
          AND d.season IN ({", ".join(season_binds)})
        ORDER BY data_year ASC, data_month ASC;
    """)
    
    df = pd.read_sql(query, _conn.engine, params=params)
    df.dropna(subset=['data_year', 'data_month'], how='all', inplace=True)
    if df.empty:
        return {"years": [], "months": []}
        
    # Extract unique components and cast to pure Python integers
    return {
        "years": df['data_year'].astype(int).unique().tolist(),
        "months": df['data_month'].astype(int).unique().tolist()
    }