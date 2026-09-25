import streamlit as st
from utils.db_conn import fetch_query
from queries.postegre_queries import GET_REGIONS_QUERY, GET_GAS_COLUMNS_QUERY,PORT_TIME_COLUMN_QUERY,PORT_COLUMNS_QUERY
import pandas as pd

# ttl=86400 means the cache lives for 24 hours. 
# It hits MotherDuck ONCE a day, costing you fractions of a penny.
@st.cache_data(ttl=86400) 
def get_cached_regions(_conn):
    df = fetch_query(_conn, GET_REGIONS_QUERY)
    if df is not None and not df.empty:
        return sorted(df['Region'].tolist())
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

