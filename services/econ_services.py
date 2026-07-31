import pandas as pd
from utils.db_conn import fetch_query
from queries.sql_queries import (
    AIR_POL_QUERY,
    MAIN_ECON_ACTIVITY,
    GET_DISTINCT_YEARS_QUERY,
    SUB_ECON_QUERY,
    ECON_ACTIVITY_QUERY
)

def get_cached_years(_conn) -> list:
    """Fetches the distinct chronological boundaries."""
    df = fetch_query(_conn, GET_DISTINCT_YEARS_QUERY)
    if df is not None and not df.empty:
        return df['Year'].dropna().tolist()
    return []

def get_cached_pollutants(_conn) -> list:
    """Fetches valid air pollutant columns for structural whitelisting."""
    df = fetch_query(_conn, AIR_POL_QUERY)
    if df is not None and not df.empty:
        return df['column_name'].tolist()
    return []

def get_cached_main_activities(_conn) -> pd.DataFrame:
    """Fetches the master dataframe of main economic activities."""
    return fetch_query(_conn, MAIN_ECON_ACTIVITY)
    
def get_cached_sub_activities(_conn, code_name: str) -> list:
    """
    Safely retrieves sub-economic activities using true parameter binding.
    """
    if not code_name:
        return []
    
    df = fetch_query(_conn,SUB_ECON_QUERY, params=(code_name,))
    if df is not None and not df.empty:
        return df['economic activity'].tolist()
    return []

def fetch_aggregated_econ_data(
    _conn, 
    activities: list, 
    pollutant: str, 
    start_year: int, 
    end_year: int, 
    valid_pollutants: list
) -> pd.DataFrame:
    """
    Executes the analytical query using strict structural validation 
    for the column name and parameterization for the WHERE clauses.
    """
    # 1. Structural Whitelisting
    if pollutant not in valid_pollutants:
        raise ValueError("Security Alert: Invalid pollutant identifier")
    
    
    if not activities:
        return pd.DataFrame()

    # 2. Parameter Binding Preparation
    placeholders = ", ".join(["?"] * len(activities))
    
    # Safely injecting the validated column name directly
    query = ECON_ACTIVITY_QUERY.format(
        air_pollutant=pollutant, 
        placeholders=placeholders
    )
    params = tuple(activities) + (start_year, end_year)
    return fetch_query(_conn, query, params=params)