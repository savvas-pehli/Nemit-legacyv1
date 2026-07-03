import streamlit as st
#import psutil as ps
from utils.db_conn import get_db_connection, fetch_query, format_in_clause
from utils.processing import check_region,check_prefecture
from queries.sql_queries import (
    GET_FUEL_REGIONS_QUERY,
    GET_FUEL_PREFECTURES_BY_REGIONS_QUERY,GET_ALL_FUEL_PREFECTURES_QUERY,
    GET_FUEL_COLUMNS_QUERY,
    GET_FUEL_DATA,
    GET_YEAR_RANGE_FUEL_QUERY
    #CHECK_GAS_VALIDITY
)
from utils.plotting import fuel_con_groupby_bar_chart


conn = get_db_connection()
st.set_page_config(
    layout="wide", page_title="Fuel Consumption Data Dashboard")
st.sidebar.title('Time and gas filters')

regions = fetch_query(conn, GET_FUEL_REGIONS_QUERY)['Region'].tolist()
selected_regions = st.multiselect("Please select Region/s:", sorted(regions),max_selections=3)
st.write('Check this box in order to get the data about the regions')
region_check=st.checkbox(
    "Regions", 
    value=False, 
    key="region_checked", 
    on_change=check_region
)



if selected_regions:
    region_clause = format_in_clause(selected_regions)
    prefecture_query = GET_FUEL_PREFECTURES_BY_REGIONS_QUERY.format(regions=region_clause)
    prefectures = fetch_query(conn, prefecture_query)['Prefecture'].tolist()
else:
    prefectures = fetch_query(conn, GET_ALL_FUEL_PREFECTURES_QUERY)['Prefecture'].tolist()
prefectures=[prefecture.capitalize() for prefecture in prefectures]
selected_prefectures = st.multiselect("Please select Prefecture/s:", sorted(prefectures), max_selections=3)



st.write('Check this box in order to get the data about prefectures')
prefecture_check=st.checkbox(
    "Prefectures", 
    value=False, # Set one to True initially
    key="prefecture_checked", 
    on_change=check_prefecture
)

# Fuel type selection
fuel_columns = fetch_query(conn, GET_FUEL_COLUMNS_QUERY)['column_name'].tolist()
selected_fuels = st.sidebar.multiselect("Select Fuel Types", fuel_columns, max_selections=2)

#timeline
year_list=fetch_query(conn,GET_YEAR_RANGE_FUEL_QUERY).iloc[0,:].tolist()
year_range = st.sidebar.slider("Years Range", year_list[0], year_list[1],(year_list[0], year_list[1]),step=1)

# in order to distinguish if the user wants to see the regional data or prefectural data
#we will have check buttons
#these buttons do not affect the timelines only the dataframes


if st.session_state.region_checked:
     main_column='Region'
     main_col_values=selected_regions
     table_name='regional_fuel_con'
elif st.session_state.prefecture_checked:
    main_column='Prefecture'
    main_col_values=selected_prefectures
    table_name='prefecture_fuel_con'
else:
    # Handle the case where the user quickly unchecks the active one before checking the other
    st.info("Please select geography")

regional_check=(st.session_state.region_checked and selected_regions)
prefectural_check=(st.session_state.prefecture_checked and selected_prefectures)

if regional_check or prefectural_check:
    
    if st.button("Run Query") and selected_fuels:
        columns = ', '.join([f'"{col}"' for col in ['Year', main_column] + selected_fuels])
        main_col_values=format_in_clause(main_col_values)
        data_query = GET_FUEL_DATA.format(
        columns=columns,
        table=table_name,
        geography=main_column,
        prefectures=main_col_values,
        start_year=year_range[0],
        end_year=year_range[-1]
    )
        df = fetch_query(conn, data_query)
        area='Region' if regional_check else 'Prefecture'
        fuel_con_groupby_bar_chart(df,area,selected_fuels)
    else:
        st.info('Please select at least one fuel type')
else:
    st.info('In order to continue please check the either the prefecture or region box and select at least one of the options you chose')

