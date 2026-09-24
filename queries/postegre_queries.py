# data/sql_queries.py (MySQL Version)

# ==Fuel consumption Queries==
GET_STATIONS_BY_REGIONS_QUERY = """
SELECT "Station" FROM public.mv_regions_station_v2 WHERE "Region" IN ({region_placeholders});
"""

GET_FUEL_REGIONS_QUERY = """
SELECT DISTINCT "Region" FROM prefecture_fuel_con; 
"""

GET_FUEL_PREFECTURES_BY_REGIONS_QUERY = """
SELECT DISTINCT "Prefecture" FROM prefecture_fuel_con WHERE "Region" IN ({region_placeholders});
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
WHERE table_schema = 'public'
  AND table_name = 'prefecture_fuel_con'
  AND column_name NOT IN (
    'Year','Prefecture','Region',
    'Total Sum'
  );
"""

GET_FUEL_DATA = """
SELECT {columns}
FROM {table}
WHERE "{geography}" IN ({geo_placeholders})
  AND "Year" BETWEEN :start_year AND :end_year;
"""

# == Pollution Queries ==
GET_REGIONS_QUERY = """
SELECT DISTINCT "Region" FROM public.mv_regions_station_v2; 
"""

GET_COMMON_YEARS_FOR_STATIONS = """
SELECT "Year"
FROM public.mv_station_years_v2
WHERE "Station" IN ({station_placeholders})
GROUP BY "Year"
HAVING COUNT(DISTINCT "Station") = :station_count;
"""

GET_ALL_STATIONS_QUERY = """
SELECT DISTINCT("Station") FROM public.mv_regions_station_v2;
"""

GET_AGGREGATED_DATA = """
SELECT 
    "Station",
    {timeframe} AS "record_datetime",
    {gas_aggs}
FROM "clean_v2" 
WHERE "Station" IN ({station_placeholders})
  AND "Year" BETWEEN :year_start AND :year_end
  AND "Month" BETWEEN :month_start AND :month_end
  AND "day_of_week" BETWEEN :day_start AND :day_end
GROUP BY 1, 2
ORDER BY 2 ASC;
"""

GET_AGGREGATED_DATA_MV = """
SELECT 
    "Station",
    {timeframe} AS "record_datetime",
    {gas_aggs}
FROM public.clean_v2
WHERE "Station" IN ({station_placeholders})
  AND {year_condition}
  AND "Month" BETWEEN :month_start AND :month_end
  AND "day_of_week" BETWEEN :day_start AND :day_end
GROUP BY 1, 2
ORDER BY 2 ASC;
"""

GET_AIR_POLLUTION_DATA = """
SELECT {columns}
FROM "clean_v2" 
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
  AND table_name = 'clean_v2'
  AND column_name NOT IN (
    'Year','municipality','Hour','Date','Region',
    'Month','Day','day_of_week','record_datetime','id','Station','batch_id', 'ingested_at'
  );
"""

GET_CHORO_GAS_COLUMNS_QUERY = """
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'clean_v2'
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
SELECT DISTINCT "year" as "Year" FROM gas_econ_activity
ORDER BY "Year" ASC;
"""



# == Data Extraction ==
# FORCE INDEX (idx_stat_year_month_day)




CHECK_GAS_VALIDITY = """
SELECT COUNT(*) AS count
FROM clean_v2
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
WHERE table_schema = 'public'
  AND table_name = 'gas_econ_activity' 
  AND column_name NOT IN ('code name','year','economic activity');
"""
                   
MAIN_ECON_ACTIVITY = """
SELECT DISTINCT "economic activity", "code name" 
FROM gas_econ_activity 
WHERE LENGTH(TRIM("code name")) < 2;
"""

SUB_ECON_QUERY = """
SELECT DISTINCT "economic activity" 
FROM gas_econ_activity
WHERE TRIM("code name") LIKE :code_name || '%' 
  AND LENGTH(TRIM("code name")) > 1;
"""

ECON_ACTIVITY_QUERY = """
SELECT "year", "economic activity", "{air_pollutant}" 
FROM gas_econ_activity 
WHERE "economic activity" IN ({act_placeholders}) 
  AND "year" BETWEEN :start_year AND :end_year;
"""

# =====LIMANI Queries=======
PORT_AGGREGATION_QUERY = """
SELECT 
    {time_expr} AS time_bucket,
    {agg_columns}
FROM public.{target_table}
WHERE EXTRACT(YEAR FROM "{time_col}") BETWEEN :start_year AND :end_year
  AND EXTRACT(MONTH FROM "{time_col}") BETWEEN :start_month AND :end_month
  AND EXTRACT(ISODOW FROM "{time_col}") BETWEEN :start_day AND :end_day
GROUP BY 1
ORDER BY 1 ASC;
"""
    
PORT_COLUMNS_QUERY = """
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = '{table_name}'
  AND column_name NOT IN ('Datetime','Date');
"""


PORT_METRICS_COLUMN_QUERY = """
SELECT column_name 
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = :target_table 
  AND data_type IN ('double precision', 'real', 'integer', 'numeric', 'bigint')
  AND column_name != :time_col;
"""

PORT_TIME_COLUMN_QUERY = """
SELECT column_name 
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = :target_table 
  AND data_type IN ('timestamp without time zone', 'timestamp with time zone', 'date');
"""
    
PORT_TIME_BOUNDARIES_QUERY = """
SELECT 
    MIN(EXTRACT(YEAR FROM "{time_col}")) AS min_y, 
    MAX(EXTRACT(YEAR FROM "{time_col}")) AS max_y 
FROM public.{target_table};
"""

NPETS_SCHEMA_QUERY = """
SELECT column_name 
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = :target_table 
  AND column_name NOT IN ('experiment_id', 'Datetime', 'Time', 'Date');
"""

NPETS_AGGREGATED_DATA_QUERY = """
SELECT 
    d.location,
    d.season,
    {time_expr} AS time_bucket,
    {agg_columns}
FROM public.{target_table} f
JOIN public.dim_experiment d ON f.experiment_id = d.experiment_id
WHERE d.location IN ({places_ph})
  AND d.season IN ({seasons_ph})
GROUP BY 1, 2, 3
ORDER BY 3 ASC;
"""

NPETS_TEMPORAL_METADATA_QUERY = """
SELECT DISTINCT 
    EXTRACT(YEAR FROM f."Datetime") AS data_year,
    EXTRACT(MONTH FROM f."Datetime") AS data_month
FROM public.{target_table} f
JOIN public.dim_experiment d ON f.experiment_id = d.experiment_id
WHERE d.location IN ({places_ph})
  AND d.season IN ({seasons_ph})
ORDER BY data_year ASC, data_month ASC;
"""