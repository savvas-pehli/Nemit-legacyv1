# data/sql_queries.py


# ==Fuel consumption Queries==
GET_FUEL_REGIONS_QUERY = """
SELECT DISTINCT Region FROM main.prefecture_fuel_con; 
"""


GET_FUEL_PREFECTURES_BY_REGIONS_QUERY = """
SELECT distinct Prefecture FROM main.prefecture_fuel_con WHERE region IN {regions};
"""

GET_ALL_FUEL_PREFECTURES_QUERY = """
SELECT distinct Prefecture FROM prefecture_fuel_con;
"""
GET_YEAR_RANGE_FUEL_QUERY="""SELECT min(year),max(year) 
FROM main.prefecture_fuel_con;"""

GET_FUEL_COLUMNS_QUERY = """
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'main'
  AND table_name = 'prefecture_fuel_con'
  AND column_name NOT IN (
    'Year','Prefecture','Region',
    'Total Sum'
  );"""


GET_FUEL_DATA = """
SELECT {columns}
FROM {table}
WHERE {geography} IN {prefectures}
  AND Year between {start_year} and {end_year};
"""
# == Region/Station Queries ==
GET_REGIONS_QUERY = """
SELECT DISTINCT region FROM new_stations_regions; 
"""

GET_STATIONS_BY_REGIONS_QUERY = """
SELECT station FROM new_stations_regions WHERE region IN ({placeholders});
"""

GET_ALL_STATIONS_QUERY = """
SELECT station FROM new_stations_regions;
"""

# == Column/Metadata ==
GET_GAS_COLUMNS_QUERY = """
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'main'
  AND table_name = 'clean'
  AND column_name NOT IN (
    'year','municipality','Hour','Date','Station','Region',
    'Month','Day','day_of_week','record_datetime','id','Year'
  );
"""
GET_CHORO_GAS_COLUMNS_QUERY = """
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'main'
  AND table_name = 'clean'
  AND column_name NOT IN (
    'year','municipality','Hour','Date','station','region','CO mg/m^3','NO mug/m^3','Benz mug/m^3',
    'Month','Day','day_of_week','record_datetime','id'
  );
"""
GET_AIR_POLLUTANTS_FOR_TABLE = """
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'main'
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
SELECT DISTINCT "Year" as Year FROM gas_econ_activity;
"""

GET_COMMON_YEARS_FOR_STATIONS = """
SELECT Year
FROM newyearstations
WHERE station IN ({placeholders})
GROUP BY Year
HAVING COUNT(DISTINCT station) = ?;
"""

# == Data Extraction ==
#to force index edo to exoum giati xoris auto an kapoios kanei search pera apo kapoia xronia tha kanei full table scan
#FORCE INDEX (idx_stat_year_month_day)
GET_AIR_POLLUTION_DATA = """
SELECT {columns}
FROM main.clean 
WHERE Station IN {stations}
  AND {year_condition}
  AND Month BETWEEN {month_start} AND {month_end}
  AND day_of_week BETWEEN {dow_start} AND {dow_end};
"""

GET_AGGREGATTED_DATA = """
SELECT 
    Station,
    {timeframe_expr} AS record_datetime,
    {gas_aggs}
FROM main.clean 
WHERE Station IN ({station_placeholders})
  AND {year_condition_expr}
  AND Month BETWEEN ? AND ?
  AND day_of_week BETWEEN ? AND ?
GROUP BY ALL
ORDER BY record_datetime ASC;
"""

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
SELECT year,Hour,municipality,"{air_pollutant}" FROM main.aggr_choro_per_hour_year
where region=?;
"""
CHOROPLETH_YEARLY_QUERY = """
SELECT year,municipality,"{air_pollutant}" FROM main.aggr_choro_per_year
where region=?;
"""

GEOMETRIC_DATA_LOAD="""SELECT * from my_db.geometries.{table}_municipalities
WHERE Municipality IN ({placeholders});"""

#ECONOMIC ACTIVITY
AIR_POL_QUERY = """SELECT column_name FROM information_schema.columns 
                   WHERE table_schema='main'
                   AND table_name='gas_econ_activity' 
                   AND column_name NOT IN ('code name','year','economic activity');"""
                   
MAIN_ECON_ACTIVITY = """SELECT DISTINCT("economic activity"), "code name" 
           FROM gas_econ_activity 
           WHERE CHAR_LENGTH("code name") < 2;"""

SUB_ECON_QUERY = """SELECT DISTINCT "economic activity" 
FROM gas_econ_activity
WHERE starts_with(trim("code name"), ?) 
  AND length(trim("code name")) > 1;"""

ECON_ACTIVITY_QUERY = """SELECT "year", "economic activity", "{air_pollutant}" 
                         FROM gas_econ_activity 
                         WHERE "economic activity" IN ({placeholders}) 
                         AND "year" BETWEEN ? AND ?
                         ORDER BY "year" ASC;"""


#=====LIMANI Queries=======
PORT_AGGREGATION_QUERY = """
            SELECT 
                {timeframe},
                {metric_aggs}
            FROM 
                thess_port_assesment.{target_table}
            WHERE 
                EXTRACT(YEAR FROM "Datetime") BETWEEN {year_range[0]} AND {year_range[1]}
                AND EXTRACT(MONTH FROM "Datetime") BETWEEN {month_range[0]} AND {month_range[1]}
                AND EXTRACT(ISODOW FROM "Datetime") BETWEEN {day_range[0]} AND {day_range[1]}
            GROUP BY ALL
            ORDER BY {timeframe_order} ASC;
        """
    
PORT_COLUMNS_QUERY = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'thess_port_assesment'
          AND table_name = '{table_name}'
          AND column_name NOT IN ('Datetime','Date')
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
