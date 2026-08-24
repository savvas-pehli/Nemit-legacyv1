# data/sql_queries.py (MySQL Version)

# ==Fuel consumption Queries==
GET_STATIONS_BY_REGIONS_QUERY = """
SELECT "station" FROM new_stations_regions WHERE "region" IN ({region_placeholders});
"""

GET_FUEL_REGIONS_QUERY = """
SELECT DISTINCT "Region" FROM prefecture_fuel_con; 
"""

GET_FUEL_PREFECTURES_BY_REGIONS_QUERY = """
SELECT DISTINCT "Prefecture" FROM prefecture_fuel_con WHERE "Region" IN {regions};
"""

GET_ALL_FUEL_PREFECTURES_QUERY = """
SELECT DISTINCT "Prefecture" FROM prefecture_fuel_con;
"""

GET_YEAR_RANGE_FUEL_QUERY = """
SELECT min("Year"), max("Year") FROM prefecture_fuel_con;
"""

GET_FUEL_COLUMNS_QUERY = """
SELECT column_name
FROM information_schema.columns
WHERE table_schema = current_database()
  AND table_name = 'prefecture_fuel_con'
  AND column_name NOT IN (
    'Year','Prefecture','Region',
    'Total Sum'
  );
"""

GET_FUEL_DATA = """
SELECT {columns}
FROM {table}
WHERE {geography} IN {prefectures}
  AND Year between {start_year} and {end_year};
"""

# == Pollution Queries ==
GET_REGIONS_QUERY = """
SELECT DISTINCT "region" FROM new_stations_regions; 
"""

GET_COMMON_YEARS_FOR_STATIONS = """
SELECT "Year"
FROM newyearstations
WHERE "station" IN ({station_placeholders})
GROUP BY "Year"
HAVING COUNT(DISTINCT "station") = :station_count;
"""

GET_ALL_STATIONS_QUERY = """
SELECT "station" FROM new_stations_regions;
"""

GET_AGGREGATTED_DATA = """
SELECT 
    "Station",
    {timeframe} AS "record_datetime",
    {gas_aggs}
FROM "clean" 
WHERE "Station" IN ({station_placeholders})
  AND "Year" BETWEEN :year_start AND :year_end
  AND "Month" BETWEEN :month_start AND :month_end
  AND "day_of_week" BETWEEN :day_start AND :day_end
GROUP BY 1, 2
ORDER BY 2 ASC;
"""

GET_AIR_POLLUTION_DATA = """
SELECT {columns}
FROM "clean" 
WHERE "Station" IN {stations}
  AND {year_condition}
  AND "Month" BETWEEN :month_start AND :month_end
  AND "day_of_week" BETWEEN :day_start AND :day_end;
"""

# == UI queries ==
GET_GAS_COLUMNS_QUERY = """
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'clean'
  AND column_name NOT IN (
    'Year','municipality','Hour','Date','station','Region',
    'Month','Day','day_of_week','record_datetime','id','Station'
  );
"""

GET_CHORO_GAS_COLUMNS_QUERY = """
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'clean'
  AND column_name NOT IN (
    'Year','municipality','Hour','Date','Station','region','CO mg/m^3','NO mug/m^3','Benz mug/m^3',
    'Month','Day','day_of_week','record_datetime','id'
  );
"""

GET_AIR_POLLUTANTS_FOR_TABLE = """
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = current_database()
  AND TABLE_NAME = '{table_name}'
  AND COLUMN_NAME NOT IN ({excluded_columns});
"""

# == Economic Activity ==
GET_ECONOMIC_ACTIVITIES_QUERY = """
SELECT DISTINCT "economic activity", "code name"
FROM gas_econ_activity
WHERE CHAR_LENGTH("code name") < 2;
"""

GET_SUB_ECONOMIC_ACTIVITIES_QUERY = """
SELECT DISTINCT "economic activity"
FROM gas_econ_activity
WHERE "code name" REGEXP '^[{code_names}]' AND CHAR_LENGTH("code name") > 1;
"""

# == Years ==
GET_DISTINCT_YEARS_QUERY = """
SELECT DISTINCT "Year" FROM gas_econ_activity;
"""



# == Data Extraction ==
# FORCE INDEX (idx_stat_year_month_day)




CHECK_GAS_VALIDITY = """
SELECT COUNT(*) AS count
FROM clean
WHERE Station IN {stations}
  AND {year_condition}
  AND Month BETWEEN {month_start} AND {month_end}
  AND day_of_week BETWEEN {dow_start} AND {dow_end}
  AND "{gas}" IS NOT NULL;
"""

# == Choropleth ==
CHOROPLETH_HOURLY_YEARLY_QUERY = """
SELECT "Year", "Hour", "municipality", "{air_pollutant}" 
FROM "aggr_choro_per_hour_year"
WHERE "Region" = :region;
"""

CHOROPLETH_YEARLY_QUERY = """
SELECT "Year", "municipality", "{air_pollutant}" 
FROM "aggr_choro_per_year"
WHERE "Region" = :region;
"""

GEOMETRIC_DATA_LOAD = """
SELECT * from public.{table}_municipalities
WHERE "Municipality" IN ({municipalities});
"""

# ECONOMIC ACTIVITY
AIR_POL_QUERY = """
SELECT column_name FROM information_schema.columns 
WHERE table_schema = current_database()
  AND table_name = 'gas_econ_activity' 
  AND column_name NOT IN ('code name','year','economic activity');
"""
                   
MAIN_ECON_ACTIVITY = """
SELECT DISTINCT "economic activity", "code name" 
FROM gas_econ_activity 
WHERE CHAR_LENGTH("code name") < 2;
"""

SUB_ECON_QUERY = """
SELECT DISTINCT "economic activity" 
FROM gas_econ_activity
WHERE TRIM("code name") LIKE CONCAT('{code_name_regex}', '%') 
  AND LENGTH(TRIM("code name")) > 1;
"""

ECON_ACTIVITY_QUERY = """
SELECT "year", "economic activity", "{air_pollutant}" 
FROM gas_econ_activity 
WHERE "economic activity" IN {econ_act_query} 
  AND "year" BETWEEN {start} AND {end};
"""

# =====LIMANI Queries=======
PORT_AGGREGATION_QUERY = """
SELECT 
    {timeframe} AS time_bucket,
    {metric_aggs}
FROM 
    thess_port_assesment.{target_table}
WHERE 
    EXTRACT(YEAR FROM Datetime) BETWEEN {year_range[0]} AND {year_range[1]}
    AND EXTRACT(MONTH FROM Datetime) BETWEEN {month_range[0]} AND {month_range[1]}
    AND EXTRACT(ISODOW FROM Datetime BETWEEN {day_range[0]} AND {day_range[1]}
GROUP BY time_bucket
ORDER BY time_bucket ASC;
"""
    
PORT_COLUMNS_QUERY = """
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'thess_port_assesment'
  AND table_name = '{table_name}'
  AND column_name NOT IN ('Datetime','Date');
"""
    
PORT_TIME_COLUMN_QUERY = """
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'thess_port_assesment'
  AND table_name = '{table_name}'
  AND data_type IN ('DATE', 'TIMESTAMP', 'DATETIME')
LIMIT 1;
"""
    
PORT_GET_TIME_BOUNDARIES_QUERY = """
SELECT 
    MIN("{time_col}") AS min_time,
    MAX("{time_col}") AS max_time
FROM thess_port_assesment.{table_name};
"""