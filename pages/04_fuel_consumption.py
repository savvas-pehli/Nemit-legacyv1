import streamlit as st
from utils.db_conn import get_db_connection
from utils.processing import check_region, check_prefecture
from services.fuel_services import (
    get_cached_regions, 
    get_cached_all_prefectures, 
    get_cached_fuel_columns, 
    get_cached_year_range,
    get_cached_prefectures_by_region,
    fetch_aggregated_fuel_data
)
from utils.plotting import fuel_con_groupby_bar_chart

st.set_page_config(layout="wide", page_title="Fuel Consumption Data Dashboard")
st.title("Fuel Consumption Analytics")
st.sidebar.title('Time and Gas Filters')

# 1. Establish Cached Resource Connection
conn = get_db_connection()

# 2. Fetch from Cache (Instantaneous)
regions = get_cached_regions(conn)
fuel_columns = get_cached_fuel_columns(conn)
year_list = get_cached_year_range(conn)

# ==============================================================================
# GEOGRAPHY FILTERS
# ==============================================================================
selected_regions = st.multiselect("Please select Region/s:", sorted(regions), max_selections=3)
region_check = st.checkbox("Enable Region Grouping", value=False, key="region_checked", on_change=check_region)

# Handle dynamic sub-queries efficiently via the service layer
if selected_regions:
    prefectures = get_cached_prefectures_by_region(conn, selected_regions)
else:
    prefectures = get_cached_all_prefectures(conn)

selected_prefectures = st.multiselect("Please select Prefecture/s:", sorted(prefectures), max_selections=3)
prefecture_check = st.checkbox("Enable Prefecture Grouping", value=False, key="prefecture_checked", on_change=check_prefecture)

# ==============================================================================
# FUEL & TIME FILTERS
# ==============================================================================
selected_fuels = st.sidebar.multiselect("Select Fuel Types", fuel_columns, max_selections=2)

year_range = st.sidebar.slider(
    "Years Range", 
    min_value=int(year_list[0]), 
    max_value=int(year_list[1]), 
    value=(int(year_list[0]), int(year_list[1])),
    step=1
)

# ==============================================================================
# EXECUTION ROUTING
# ==============================================================================
if st.session_state.region_checked:
    main_column = 'Region'
    main_col_values = selected_regions
    table_name = 'regional_fuel_con'
elif st.session_state.prefecture_checked:
    main_column = 'Prefecture'
    main_col_values = selected_prefectures
    table_name = 'prefecture_fuel_con'
else:
    main_column = None

regional_check = (st.session_state.region_checked and selected_regions)
prefectural_check = (st.session_state.prefecture_checked and selected_prefectures)


# ==============================================================================
# CACHE CONTROL
# ==============================================================================
st.sidebar.markdown("### System Controls")
if st.sidebar.button("🔄 Force Refresh Data", type="primary"):
    st.cache_data.clear()
    st.sidebar.success("Cache wiped. The next query will hit the database.")
st.sidebar.markdown("---")

if regional_check or prefectural_check:
    if st.button("Run Query", type="primary"):
        if not selected_fuels:
            st.warning('Please select at least one fuel type from the sidebar.')
            st.stop()
            
        with st.spinner("Extracting insights from warehouse..."):
            try:
                # HIT THE PARAMETERIZED SERVICE LAYER
                df = fetch_aggregated_fuel_data(
                    _conn=conn,
                    table_alias=table_name,
                    main_column=main_column,
                    main_col_values=main_col_values,
                    selected_fuels=selected_fuels,
                    start_year=year_range[0],
                    end_year=year_range[1]
                )
                
                if df is not None and not df.empty:
                    area = 'Region' if regional_check else 'Prefecture'
                    fuel_con_groupby_bar_chart(df, area, selected_fuels)
                else:
                    st.warning("No data found for the selected parameters.")
                    
            except Exception as e:
                st.error(f"Execution Error: {e}")
else:
    st.info('In order to continue, please check either the prefecture or region box and select at least one corresponding area.')