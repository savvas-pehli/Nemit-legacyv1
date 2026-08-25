# services/fuel_service.py
import streamlit as st
from utils.db_conn import fetch_query
from utils.constants import VALID_FUEL_TABLES
from queries.postegre_queries import (
    GET_FUEL_PREFECTURES_BY_REGIONS_QUERY,
    GET_FUEL_REGIONS_QUERY,
    GET_ALL_FUEL_PREFECTURES_QUERY,
    GET_FUEL_COLUMNS_QUERY,
    GET_YEAR_RANGE_FUEL_QUERY,
    GET_FUEL_DATA)
import pandas as pd

@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def get_cached_regions(_conn):
    """Fetches regions once and stores in RAM."""
    df = fetch_query(_conn, GET_FUEL_REGIONS_QUERY)
    if df is not None and not df.empty:
        return df['Region'].dropna().tolist()
    return []


@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def get_cached_all_prefectures(_conn):
    """Fetches prefectures once and stores in RAM."""
    df = fetch_query(_conn, GET_ALL_FUEL_PREFECTURES_QUERY)
    if df is not None and not df.empty:
        return [pref.capitalize() for pref in df['Prefecture'].dropna().tolist()]
    return []

@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def get_cached_fuel_columns(_conn):
    """Fetches fuel column schema once."""
    df = fetch_query(_conn, GET_FUEL_COLUMNS_QUERY)
    if df is not None and not df.empty:
        return df['column_name'].tolist()
    return []

@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def get_cached_year_range(_conn):
    """Fetches historical boundaries once."""
    df = fetch_query(_conn, GET_YEAR_RANGE_FUEL_QUERY)
    if df is not None and not df.empty:
        return df.iloc[0, :].tolist()
    return []

@st.cache_data(ttl=3600, max_entries=10, show_spinner=False)
def get_cached_prefectures_by_region(_conn, selected_regions: list):
    """
    Safely retrieves prefectures based on regions using parameterized binding.
    """
    if not selected_regions:
        return []
    
    # Dynamic Dictionary Parameter Binding
    params = {}
    ph_list = []
    for i, region in enumerate(selected_regions):
        key = f"reg_{i}"
        ph_list.append(f":{key}")
        params[key] = region
        
    placeholders = ", ".join(ph_list)
    query = GET_FUEL_PREFECTURES_BY_REGIONS_QUERY.format(region_placeholders=placeholders)
    
    df = fetch_query(_conn, query, params=params)
    if df is not None and not df.empty:
        return [pref.capitalize() for pref in df['Prefecture'].dropna().tolist()]
    return []

@st.cache_data(ttl=3600, max_entries=10, show_spinner=False)
def fetch_aggregated_fuel_data(
    _conn, 
    table_alias: str, 
    main_column: str, 
    main_col_values: list, 
    selected_fuels: list, 
    start_year: int, 
    end_year: int
) -> pd.DataFrame:
    """
    Executes the main analytical query using strict whitelisting and dictionary parameterization.
    """
    # 1. Structural Whitelisting
    if table_alias not in VALID_FUEL_TABLES:
        raise ValueError("Security Alert: Invalid table identifier")
    
    if VALID_FUEL_TABLES[table_alias] != main_column:
        raise ValueError("Security Alert: Table and geography mismatch")
        
    # Safely building the SELECT clause
    columns = ', '.join([f'"{col}"' for col in ['Year', main_column] + selected_fuels])
    
    # 2. Parameter Binding Preparation
    params = {
        "start_year": start_year,
        "end_year": end_year
    }
    
    ph_list = []
    for i, val in enumerate(main_col_values):
        key = f"geo_{i}"
        ph_list.append(f":{key}")
        params[key] = val
        
    placeholders = ", ".join(ph_list)
    
    # 3. Securely inject structural parameters into the template
    query = GET_FUEL_DATA.format(
        columns=columns,
        table=table_alias,
        geography=main_column,
        geo_placeholders=placeholders
    )
    
    return fetch_query(_conn, query, params=params)