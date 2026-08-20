import streamlit as st
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
        params = {}
        placeholders = []
        # Dynamically build named parameters: :reg_0, :reg_1, etc.
        for i, region in enumerate(regions):
            key = f"reg_{i}"
            placeholders.append(f":{key}")
            params[key] = region
            
        query = GET_STATIONS_BY_REGIONS_QUERY.format(region_placeholders=", ".join(placeholders))
        df = fetch_query(_conn, query, params=params)
        
    if df is not None and not df.empty:
        return [station.capitalize() for station in df['station'].tolist()]
    return []


def get_common_years(_conn, stations: list) -> list:
    if not stations:
        return []
    
    upper_stations = [s.upper() for s in stations]
    params = {"station_count": len(upper_stations)}
    station_placeholders = []
    
    for i, station in enumerate(upper_stations):
        key = f"stat_{i}"
        station_placeholders.append(f":{key}")
        params[key] = station
        
    st.write(station_placeholders)
    query = GET_COMMON_YEARS_FOR_STATIONS.format(station_placeholders=", ".join(station_placeholders))
    df = fetch_query(_conn, query, params=params)
    
    if df is not None and not df.empty:
        return df['Year'].tolist()
    return []

def fetch_aggregated_pollution_data(
    _conn, stations: list, gases: list, valid_gases: list, 
    year_range, month_range: list, day_range: list, 
    timeframe: str, agg_method: str
) -> pd.DataFrame:
    
    if not stations or not gases:
        return pd.DataFrame()
        
    for gas in gases:
        if gas not in valid_gases:
            raise ValueError(f"Security Alert: Invalid gas identifier '{gas}'")

    sql_timeframe = {
        "Year": 'EXTRACT(YEAR FROM "record_datetime")',
        "Month": 'EXTRACT(MONTH FROM "record_datetime")',
        "Day": 'EXTRACT(ISODOW FROM "record_datetime")',
        "Hour": 'EXTRACT(HOUR FROM "record_datetime")'
    }
    sql_agg = {"Mean": 'AVG("{gas}")', "Median": 'percentile_cont(0.5) WITHIN GROUP (ORDER BY "{gas}")'}
    
    timeframe_expr = sql_timeframe.get(timeframe)
    gas_aggs = ', '.join([f'{sql_agg[agg_method].format(gas=gas)} AS "{gas}"' for gas in gases])
    
    # Base parameters mapping exactly to the SQL template
    params = {
        "month_start": month_range[0],
        "month_end": month_range[1],
        "day_start": day_range[0],
        "day_end": day_range[1]
    }
    
    # Strict Station Mapping
    upper_stations = [s.upper() for s in stations]
    stat_placeholders = []
    for i, stat in enumerate(upper_stations):
        key = f"stat_{i}"
        stat_placeholders.append(f":{key}")
        params[key] = stat
        
    # Strict Year Mapping
    if isinstance(year_range, tuple):
        year_condition_expr = '"year" BETWEEN :year_start AND :year_end'
        params["year_start"] = year_range[0]
        params["year_end"] = year_range[1]
    else:
        year_placeholders = []
        for i, yr in enumerate(year_range):
            key = f"yr_{i}"
            year_placeholders.append(f":{key}")
            params[key] = yr
        year_condition_expr = f'"year" IN ({", ".join(year_placeholders)})'
        
    query = GET_AGGREGATTED_DATA.format(
        timeframe=timeframe_expr,
        gas_aggs=gas_aggs,
        station_placeholders=", ".join(stat_placeholders),
        year_condition=year_condition_expr
    )
    
    return fetch_query(_conn, query, params=params)