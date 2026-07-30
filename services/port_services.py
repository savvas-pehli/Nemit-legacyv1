import streamlit as st
from utils.UI import get_port_table_columns, get_port_time_column_metadata, get_dynamic_year_bounds

@st.cache_data(ttl=86400, max_entries=5)
def get_cached_port_metadata(_conn, target_table):
    """Caches the schema lookup for the time column. Max 5 entries."""
    return get_port_time_column_metadata(_conn, target_table)

@st.cache_data(ttl=86400, max_entries=5)
def get_cached_year_bounds(_conn, target_table, time_col_name):
    """Caches the min/max year boundaries. Max 5 entries."""
    return get_dynamic_year_bounds(_conn, target_table, time_col_name)

@st.cache_data(ttl=86400, max_entries=5)
def get_cached_port_columns(_conn, target_table):
    """Caches the available metrics for the multiselect dropdown. Max 5 entries."""
    return get_port_table_columns(_conn, table_name=target_table)