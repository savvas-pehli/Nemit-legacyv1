import pandas as pd
from utils.db_conn import fetch_query
from queries.sql_queries import (
    GET_STATIONS_BY_REGIONS_QUERY,
    GET_COMMON_YEARS_FOR_STATIONS,
    GET_ALL_STATIONS_QUERY,
    GET_AGGREGATTED_DATA
)

def get_stations_by_regions(_conn, regions: list) -> list:
    if not regions:
        df = fetch_query(_conn, GET_ALL_STATIONS_QUERY)
    else:
        placeholders = ", ".join(["?"] * len(regions))
        query = GET_STATIONS_BY_REGIONS_QUERY.format(placeholders=placeholders)
        df = fetch_query(_conn, query, params=tuple(regions))
        
    if df is not None and not df.empty:
        return [station.capitalize() for station in df['station'].tolist()]
    return []

def get_common_years(_conn, stations: list) -> list:
    if not stations:
        return []
    
    # The database stores stations in uppercase based on your original logic
    upper_stations = [s.upper() for s in stations]
    placeholders = ", ".join(["?"] * len(upper_stations))
    
    query = GET_COMMON_YEARS_FOR_STATIONS.format(placeholders=placeholders)
    # The last parameter is for the HAVING COUNT() = ?
    params = tuple(upper_stations) + (len(upper_stations),)
    
    df = fetch_query(_conn, query, params=params)
    if df is not None and not df.empty:
        return df['Year'].tolist()
    return []

def fetch_aggregated_pollution_data(
    _conn, stations: list, gases: list, valid_gases: list, 
    year_range, month_range: list, day_range: list, 
    timeframe: str, agg_method: str
) -> pd.DataFrame:
    
    # 1. Structural Validation
    if not stations or not gases:
        return pd.DataFrame()
        
    for gas in gases:
        if gas not in valid_gases:
            raise ValueError(f"Security Alert: Invalid gas identifier '{gas}'")

    # 2. Structural Injection (Timeframes & Aggregations)
    sql_timeframe = {
        "Year": "EXTRACT(YEAR FROM record_datetime)",
        "Month": "EXTRACT(MONTH FROM record_datetime)",
        "Day": "EXTRACT(ISODOW FROM record_datetime)",
        "Hour": "EXTRACT(HOUR FROM record_datetime)"
    }
    sql_agg = {"Mean": "AVG", "Median": "MEDIAN"}
    
    timeframe_expr = sql_timeframe.get(timeframe)
    gas_aggs = ', '.join([f'{sql_agg[agg_method]}("{gas}") AS "{gas}"' for gas in gases])
    
    # 3. Parameter Binding Preparation
    upper_stations = [s.upper() for s in stations]
    station_placeholders = ", ".join(["?"] * len(upper_stations))
    params = tuple(upper_stations)
    
    # Year Logic handling (Between vs IN)
    if isinstance(year_range, tuple):
        year_condition_expr = "Year BETWEEN ? AND ?"
        params += (year_range[0], year_range[1])
    else:
        year_placeholders = ", ".join(["?"] * len(year_range))
        year_condition_expr = f"Year IN ({year_placeholders})"
        params += tuple(year_range)
        
    # Add Month and Day ranges
    params += (month_range[0], month_range[1], day_range[0], day_range[1])
    
    query = GET_AGGREGATTED_DATA.format(
        timeframe_expr=timeframe_expr,
        gas_aggs=gas_aggs,
        station_placeholders=station_placeholders,
        year_condition_expr=year_condition_expr
    )
    
    return fetch_query(_conn, query, params=params)