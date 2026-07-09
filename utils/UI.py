import streamlit as st
from utils.db_conn import fetch_query
from queries.sql_queries import GET_REGIONS_QUERY, GET_GAS_COLUMNS_QUERY,PORT_TIME_COLUMN_QUERY,PORT_COLUMNS_QUERY
import pandas as pd
from queries.sql_queries import PORT_GET_TIME_BOUNDARIES_QUERY

# ttl=86400 means the cache lives for 24 hours. 
# It hits MotherDuck ONCE a day, costing you fractions of a penny.
@st.cache_data(ttl=86400) 
def get_cached_regions(_conn):
    df = fetch_query(_conn, GET_REGIONS_QUERY)
    if df is not None and not df.empty:
        return sorted(df['region'].tolist())
    return []

@st.cache_data(ttl=86400)
def get_cached_gases(_conn):
    df = fetch_query(_conn, GET_GAS_COLUMNS_QUERY)
    if df is not None and not df.empty:
        return df['column_name'].tolist()
    return []
@st.cache_data(ttl=86400)
def get_port_time_column_metadata(_conn, table_name):
    """
    Introspects the table to find the primary time column and its data type.
    Assumes your tables have one primary time column of type DATE, TIMESTAMP, or DATETIME.
    """
    query =PORT_TIME_COLUMN_QUERY.format(table_name=table_name)
    df = fetch_query(_conn, query)
    
    if df is not None and not df.empty:
        col_name = df['column_name'].iloc[0]
        col_type = df['data_type'].iloc[0]
        return col_name, col_type
    
    # Fallback if somehow a table has no date column
    return None, None

@st.cache_data(ttl=86400)
def get_port_table_columns(_conn, table_name):
    """Fetches the available metrics for the selected analysis type."""
    # We query the information schema to get the actual gas/particle column names
    query =PORT_COLUMNS_QUERY.format(table_name=table_name)
    df = fetch_query(_conn, query)
    if df is not None and not df.empty:
        return df['column_name'].tolist()
    return []

@st.cache_data(ttl=86400)
def get_dynamic_year_bounds(_conn, table_name, time_col_name):
    """
    Extracts the minimum and maximum years from the target table.
    Caches the boundaries to prevent redundant full-table scans.
    """
    query = PORT_GET_TIME_BOUNDARIES_QUERY.format(
        time_col=time_col_name, 
        table_name=table_name
    )
    
    df = fetch_query(_conn, query)
    
    # Defensive check: Ensure dataframe is valid and not empty (e.g., table has no rows)
    if df is not None and not df.empty and pd.notna(df['min_time'].iloc[0]):
        # Convert strings to Pandas datetime objects
        min_date = pd.to_datetime(df['min_time'].iloc[0])
        max_date = pd.to_datetime(df['max_time'].iloc[0])
        
        return {
            "min_year": int(min_date.year),
            "max_year": int(max_date.year)
        }
        
    # Fallback failsafe if the database returns an empty payload
    return {"min_year": 2020, "max_year": 2026}