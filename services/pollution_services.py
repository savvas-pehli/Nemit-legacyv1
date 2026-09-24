import pandas as pd
from sqlalchemy import text
from utils.db_conn import fetch_query
import streamlit as st
from queries.postegre_queries import (
    GET_STATIONS_BY_REGIONS_QUERY,
    GET_COMMON_YEARS_FOR_STATIONS,
    GET_ALL_STATIONS_QUERY,
    GET_AGGREGATED_DATA)

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
        # RETURN RAW STRINGS. DO NOT MUTATE.
        return df['Station'].tolist() 
    return []


def get_common_years(_conn, stations: list) -> list:
    if not stations:
        return []
    
    
    params = {"station_count": len(stations)}
    station_placeholders = []
    
    for i, station in enumerate(stations):
        key = f"stat_{i}"
        station_placeholders.append(f":{key}")
        params[key] = station
        
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

    # ==============================================================================
    # DYNAMIC SQL GENERATOR (Targeting clean_v2)
    # ==============================================================================
    
    # 1. Map Streamlit Timeframes to PostgreSQL DATE_TRUNC
    sql_timeframe = {
        "Year": 'EXTRACT(YEAR FROM "record_datetime")',
        "Month": 'EXTRACT(MONTH FROM "record_datetime")',
        # ISODOW returns 1=Monday to 7=Sunday, perfectly matching your DAYS_MAP
        "Day": 'EXTRACT(ISODOW FROM "record_datetime")', 
        "Hour": 'EXTRACT(HOUR FROM "record_datetime")'
    }
    timeframe_expr = sql_timeframe.get(timeframe, "record_datetime")

    # 2. Map Aggregation Method to PostgreSQL Syntax
    agg_sqls = []
    for gas in gases:
        safe_gas = f'"{gas}"' # Double quotes for case-sensitivity
        
        if agg_method == "Mean":
            agg_sqls.append(f'ROUND(AVG({safe_gas})::numeric, 2) AS {safe_gas}')
        elif agg_method == "Median":
            # Native PostgreSQL Median calculation
            agg_sqls.append(f'PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {safe_gas}) AS {safe_gas}')
            
    gas_aggs = ",\n    ".join(agg_sqls)

    # ==============================================================================
    # EXACT PARAMETER BINDING 
    # ==============================================================================
    params = {
        "month_start": month_range[0],
        "month_end": month_range[1],
        "day_start": day_range[0],
        "day_end": day_range[1]
    }
    
    stat_placeholders = []
    for i, stat in enumerate(stations):
        key = f"stat_{i}"
        stat_placeholders.append(f":{key}")
        params[key] = stat
        
    if isinstance(year_range, tuple):
        year_condition_expr = '"Year" BETWEEN :year_start AND :year_end'
        params["year_start"] = year_range[0]
        params["year_end"] = year_range[1]
    else:
        year_placeholders = []
        for i, yr in enumerate(year_range):
            key = f"yr_{i}"
            year_placeholders.append(f":{key}")
            params[key] = yr
        year_condition_expr = f'"Year" IN ({", ".join(year_placeholders)})'
        
    query = GET_AGGREGATED_DATA.format(
        timeframe=timeframe_expr,
        gas_aggs=gas_aggs,
        station_placeholders=", ".join(stat_placeholders),
        year_condition=year_condition_expr
    )
    return fetch_query(_conn, query, params=params)