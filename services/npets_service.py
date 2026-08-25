import pandas as pd
import streamlit as st
from utils.db_conn import fetch_query, format_in_clause
from queries.postegre_queries import (
    NPETS_SCHEMA_QUERY,
    NPETS_AGGREGATED_DATA_QUERY,
    NPETS_TEMPORAL_METADATA_QUERY
)
# ==============================================================================
# CONFIGURATION & WHITELISTS (Decoupling logic from the UI)
# ==============================================================================
VALID_TOOLS = {
    "ELPI": "elpi",
    "OPS": "ops",
    "METADATA": "metadata"
}

# PostgreSQL-compliant time extraction
PG_TIMEFRAME = {
    "Day": '(EXTRACT(ISODOW FROM f."Datetime") - 1)', # Maps 1-7 (Mon-Sun) down to 0-6 to match UI map
    "Hour": 'EXTRACT(HOUR FROM f."Datetime")'
}

def get_npets_schema(conn, tool_name: str) -> list:
    """
    Interrogates the PostgreSQL Information Schema to dynamically return 
    measurement columns using strict binding.
    """
    if tool_name not in VALID_TOOLS:
        raise ValueError(f"Security Alert: Invalid tool '{tool_name}'")
        
    target_table = VALID_TOOLS[tool_name]
    
    # We pass the table name as a safe bound parameter
    df = fetch_query(conn, NPETS_SCHEMA_QUERY, params={"target_table": target_table})    
    if df is not None and not df.empty:
        return df['column_name'].tolist()
    return []

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_aggregated_npets_data(
    _conn,
    agg_type: str,
    tool_name: str, 
    places: list, 
    seasons: list, 
    measurements: list, 
    timeframe: str
) -> pd.DataFrame:
    """
    Executes the analytical JOIN query utilizing dictionary parameters and PG syntax.
    """
    if tool_name not in VALID_TOOLS:
        raise ValueError("Security Alert: Invalid tool identifier")
    if timeframe not in PG_TIMEFRAME:
        raise ValueError("Security Alert: Invalid timeframe identifier")
        
    target_table = VALID_TOOLS[tool_name]
    time_expr = PG_TIMEFRAME[timeframe]
    
    if agg_type == 'Mean':
        agg_columns = ", ".join([f'AVG(f."{m}") AS "{m}"' for m in measurements])
    elif agg_type == 'Median':
        agg_columns = ", ".join([f'PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f."{m}") AS "{m}"' for m in measurements])
    else:
        raise ValueError("Security Alert: Invalid aggregation method")
    
    params = {}
    
    # Bind Places dynamically
    ph_places = []
    for i, place in enumerate(places):
        key = f"place_{i}"
        ph_places.append(f":{key}")
        params[key] = place
        
    # Bind Seasons dynamically
    ph_seasons = []
    for i, season in enumerate(seasons):
        key = f"season_{i}"
        ph_seasons.append(f":{key}")
        params[key] = season.upper()
    
    query = NPETS_AGGREGATED_DATA_QUERY.format(
        target_table=target_table,
        time_expr=time_expr,
        agg_columns=agg_columns,
        places_ph=", ".join(ph_places),
        seasons_ph=", ".join(ph_seasons)
    )    
    
    return fetch_query(_conn, query, params=params)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_temporal_metadata(
    _conn, 
    tool_name: str, 
    places: list, 
    seasons: list
) -> dict:
    """
    Executes a high-speed DISTINCT scan using strict dictionary binding.
    """
    if tool_name not in VALID_TOOLS:
        raise ValueError("Security Alert: Invalid tool identifier")
        
    target_table = VALID_TOOLS[tool_name]
    params = {}
    
    ph_places = []
    for i, place in enumerate(places):
        key = f"place_{i}"
        ph_places.append(f":{key}")
        params[key] = place
        
    ph_seasons = []
    for i, season in enumerate(seasons):
        key = f"season_{i}"
        ph_seasons.append(f":{key}")
        params[key] = season.upper()
    
    query = NPETS_TEMPORAL_METADATA_QUERY.format(
        target_table=target_table,
        places_ph=", ".join(ph_places),
        seasons_ph=", ".join(ph_seasons)
    )
    
    df = fetch_query(_conn, query, params=params)
    
    if df is None or df.empty:
        return {"years": [], "months": []}
        
    df.dropna(subset=['data_year', 'data_month'], how='all', inplace=True)
    
    return {
        "years": df['data_year'].astype(int).unique().tolist(),
        "months": df['data_month'].astype(int).unique().tolist()
    }