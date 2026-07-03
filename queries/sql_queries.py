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
SELECT station FROM new_stations_regions WHERE region IN {regions};
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
    'year','municipality','Hour','Date','station','region',
    'Month','Day','day_of_week','record_datetime','id'
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
SELECT DISTINCT "Year" FROM gas_econ_activity;
"""

GET_COMMON_YEARS_FOR_STATIONS = """
SELECT Year
FROM newyearstations
WHERE station IN {stations}
GROUP BY Year
HAVING COUNT(DISTINCT station) = {station_count};
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
where region={region};
"""
CHOROPLETH_YEARLY_QUERY = """
SELECT year,municipality,'{air_pollutant}' FROM main.aggr_choro_per_year
where region={region};
"""

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
WHERE starts_with(trim("code name"), '{code_name_regex}') 
  AND length(trim("code name")) > 1;"""

ECON_ACTIVITY_QUERY = """SELECT "year", "economic activity", "{air_pollutant}" 
                         FROM gas_econ_activity 
                         WHERE "economic activity" IN {econ_act_query} 
                         AND "year" BETWEEN {start} AND {end}"""