import pandas as pd
from utils.db_conn import fetch_query
from utils.translation_helper import greek_to_latin
from queries.sql_queries import (
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
    placeholders = ", ".join(["?"] * len(municipality_ids))
    
    query = GEOMETRIC_DATA_LOAD.format(
        table=table_name,
        placeholders=placeholders
    )
    
    return fetch_query(_conn, query, params=tuple(municipality_ids))

def fetch_choropleth_data(_conn, region: str, pollutant: str, timeframe: str, valid_pollutants: list) -> pd.DataFrame:
    """
    Executes the analytical query using structural validation and true parameterization.
    """
    if pollutant not in valid_pollutants:
        raise ValueError("Security Alert: Invalid pollutant identifier")
        
    # Determine the correct query based on the selected timeframe
    if timeframe == "Yearly timeframe":
        query_template = CHOROPLETH_YEARLY_QUERY
    else:
        query_template = CHOROPLETH_HOURLY_YEARLY_QUERY
        
    query = query_template.format(air_pollutant=pollutant)
    
    # Execute with true parameter binding for the region
    return fetch_query(_conn, query, params=(region,))