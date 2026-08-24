import pandas as pd
from utils.db_conn import fetch_query
from utils.translation_helper import greek_to_latin
import streamlit as st
from queries.postegre_queries import (
    GET_CHORO_GAS_COLUMNS_QUERY,
    CHOROPLETH_YEARLY_QUERY,
    CHOROPLETH_HOURLY_YEARLY_QUERY,
    GEOMETRIC_DATA_LOAD
)

def get_cached_choro_columns(_conn) -> list:
    """Fetches the allowed pollutant columns for the map."""
    df = fetch_query(_conn, GET_CHORO_GAS_COLUMNS_QUERY)
    if df is not None and not df.empty:
        return df['column_name'].tolist()
    return []

def get_cached_geometric_data(_conn, region: str, raw_municipalities: list) -> pd.DataFrame:
    """
    Translates the Greek municipalities, builds the parameter markers, 
    and securely fetches the geometry data.
    """
    if not raw_municipalities:
        return pd.DataFrame()
        
    # Translate and get unique IDs
    municipality_ids = list(set([greek_to_latin(m) for m in raw_municipalities]))
    table_name = region.replace(" ", "_")
    params = {}
    ph_list = []
    for i, muni in enumerate(municipality_ids):
        key = f"muni_{i}"
        ph_list.append(f":{key}")
        params[key] = muni
        
    query = GEOMETRIC_DATA_LOAD.format(
        table=table_name,
        municipalities=", ".join(ph_list)
    )
    return fetch_query(_conn, query, params=params)

def fetch_choropleth_data(_conn, region: str, pollutant: str, timeframe: str, valid_pollutants: list) -> pd.DataFrame:
    """
    Executes the analytical query using structural validation and true dictionary parameterization.
    """
    if pollutant not in valid_pollutants:
        raise ValueError("Security Alert: Invalid pollutant identifier")
        
    # Determine the correct query based on the selected timeframe
    if timeframe == "Yearly timeframe":
        query_template = CHOROPLETH_YEARLY_QUERY
    else:
        query_template = CHOROPLETH_HOURLY_YEARLY_QUERY
    
    # 1. Inject the column name (Structural formatting)
    query = query_template.format(air_pollutant=pollutant)
    
    # 2. Execute with strict dictionary binding (Data formatting)
    return fetch_query(_conn, query, params={"region": region})