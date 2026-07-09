import streamlit as st
from utils.db_conn import fetch_query
from queries.sql_queries import GET_REGIONS_QUERY, GET_GAS_COLUMNS_QUERY

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