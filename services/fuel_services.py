# services/fuel_service.py
import streamlit as st
from utils.db_conn import fetch_query
from queries.sql_queries import (
    GET_FUEL_REGIONS_QUERY,
    GET_ALL_FUEL_PREFECTURES_QUERY,
    GET_FUEL_COLUMNS_QUERY,
    GET_YEAR_RANGE_FUEL_QUERY
)

@st.cache_data(ttl=86400) # Cache expires after 24 hours
def get_cached_regions(_conn):
    """Fetches regions once and stores in RAM."""
    df = fetch_query(_conn, GET_FUEL_REGIONS_QUERY)
    return df['Region'].tolist()

@st.cache_data(ttl=86400)
def get_cached_all_prefectures(_conn):
    """Fetches prefectures once and stores in RAM."""
    df = fetch_query(_conn, GET_ALL_FUEL_PREFECTURES_QUERY)
    return [pref.capitalize() for pref in df['Prefecture'].tolist()]

@st.cache_data(ttl=86400)
def get_cached_fuel_columns(_conn):
    """Fetches fuel column schema once."""
    df = fetch_query(_conn, GET_FUEL_COLUMNS_QUERY)
    return df['column_name'].tolist()

@st.cache_data(ttl=86400)
def get_cached_year_range(_conn):
    """Fetches historical boundaries once."""
    df = fetch_query(_conn, GET_YEAR_RANGE_FUEL_QUERY)
    return df.iloc[0, :].tolist()