# services/fuel_service.py
import streamlit as st
from utils.db_conn import fetch_query
from utils.constants import VALID_FUEL_TABLES
from queries.mysql_queries import (
    GET_FUEL_REGIONS_QUERY,
    GET_ALL_FUEL_PREFECTURES_QUERY,
    GET_FUEL_COLUMNS_QUERY,
    GET_YEAR_RANGE_FUEL_QUERY)
import pandas as pd

@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def get_cached_regions(_conn):
    """Fetches regions once and stores in RAM."""
    df = fetch_query(_conn, GET_FUEL_REGIONS_QUERY)
    return df['Region'].tolist()

@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def get_cached_all_prefectures(_conn):
    """Fetches prefectures once and stores in RAM."""
    df = fetch_query(_conn, GET_ALL_FUEL_PREFECTURES_QUERY)
    return [pref.capitalize() for pref in df['Prefecture'].tolist()]

@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def get_cached_fuel_columns(_conn):
    """Fetches fuel column schema once."""
    df = fetch_query(_conn, GET_FUEL_COLUMNS_QUERY)
    return df['column_name'].tolist()

@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def get_cached_year_range(_conn):
    """Fetches historical boundaries once."""
    df = fetch_query(_conn, GET_YEAR_RANGE_FUEL_QUERY)
    return df.iloc[0, :].tolist()

@st.cache_data(ttl=3600, max_entries=10, show_spinner=False)
def get_cached_prefectures_by_region(_conn, selected_regions: list):
    """
    Safely retrieves prefectures based on regions using parameterized binding.
    """
    if not selected_regions:
        return []
    
    # Generate exact number of placeholders: (?, ?, ?)
    placeholders = ", ".join(["?"] * len(selected_regions))
    
    query = f"""
        SELECT DISTINCT Prefecture 
        FROM main.prefecture_fuel_con
        WHERE Region IN ({placeholders})
    """
    # Pass the list of regions as the parameter tuple
    
    df = _conn.execute(query, tuple(selected_regions)).df()
    return [pref.capitalize() for pref in df['Prefecture'].tolist()]

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
    Executes the main analytical query using strict whitelisting and parameterization.
    """
    # 1. Structural Whitelisting
    if table_alias not in VALID_FUEL_TABLES:
        raise ValueError("Security Alert: Invalid table identifier")
    
    if VALID_FUEL_TABLES[table_alias] != main_column:
        raise ValueError("Security Alert: Table and geography mismatch")
        
    # Safely building the SELECT clause
    columns = ', '.join([f'"{col}"' for col in ['Year', main_column] + selected_fuels])
    
    # 2. Parameter Binding Preparation
    placeholders = ", ".join(["?"] * len(main_col_values))
    
    query = f"""
        SELECT {columns}
        FROM {table_alias}
        WHERE "{main_column}" IN ({placeholders})
          AND Year BETWEEN ? AND ?
    """
    
    # Pack all values into a single tuple for the execution engine
    params = tuple(main_col_values) + (start_year, end_year)
    
    return _conn.execute(query, params).df()