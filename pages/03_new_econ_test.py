import numpy as np
import plotly.express as px
import streamlit as st
from services.econ_services import (
    fetch_aggregated_econ_data,
    get_cached_main_activities,
    get_cached_pollutants,
    get_cached_sub_activities,
    get_cached_years,
)
from utils.db_conn import get_database_engine

st.set_page_config(
    layout="wide", page_title="Economic Activity Pollution", page_icon="📈"
)
st.title("Economic Activity Pollution Dashboard")

# ==============================================================================
# CACHE CONTROL
# ==============================================================================
st.sidebar.markdown("### System Controls")
if st.sidebar.button("🔄 Force Refresh Data", type="primary"):
    st.cache_data.clear()
    st.sidebar.success("Cache wiped. The next query will hit the database.")
st.sidebar.markdown("---")

conn = get_database_engine()

# ==============================================================================
# METADATA RETRIEVAL
# ==============================================================================
year_list = get_cached_years(conn)
if not year_list:
    st.error(
        "Failed to load timeline boundaries from database. Please refresh the page."
    )
    st.stop()

valid_pollutants = get_cached_pollutants(conn)
if not valid_pollutants:
    st.error("Fatal Error: Failed to load pollutant schema.")
    st.stop()

# ==============================================================================
# UI FILTERS
# ==============================================================================
st.sidebar.title("Time and Gas Filters")

years_selected = st.sidebar.select_slider(
    "Choose year range",
    options=np.sort(year_list),
    value=(min(year_list), max(year_list)),
)

air_pollutant = st.sidebar.selectbox("Select Air Pollutant", options=valid_pollutants)

# Fetch Activity Metadata
main_activities_df = get_cached_main_activities(conn)
if main_activities_df is None or main_activities_df.empty:
    st.warning("No economic activities found in the warehouse.")
    st.stop()

econ_act = st.multiselect(
    "Select Main Economic Activity (Max 5)",
    options=np.sort(main_activities_df["economic activity"].tolist()),
    max_selections=5,
)

st.markdown("---")
st.info(
    "Select exactly **one** main economic activity to unlock granular sub-activity metrics."
)

sub_econ_act = []
if len(econ_act) == 1:
    enable_sub_selection = st.checkbox("Enable Sub-Economic Activity Selection")

    if enable_sub_selection:
        # Extract the correct code name for the selected activity
        target_code_name = main_activities_df.loc[
            main_activities_df["economic activity"] == econ_act[0], "code name"
        ].iloc[0]

        # Hit the service layer to get matching sub-activities
        sub_list_options = get_cached_sub_activities(conn, code_name=target_code_name)

        if sub_list_options:
            sub_econ_act = st.multiselect(
                "Select Sub-Economic Activities (Max 5)",
                options=np.sort(sub_list_options),
                max_selections=5,
            )
        else:
            st.warning("No sub-activities found for this selection.")
elif len(econ_act) > 1:
    st.warning(
        "⚠️ Sub-economic activity selection is disabled when multiple main activities are chosen."
    )

# ==============================================================================
# EXECUTION ROUTING
# ==============================================================================
all_activities = econ_act + sub_econ_act

if st.button("Generate Analysis", type="primary"):
    if not all_activities:
        st.warning("Please select at least one economic activity to proceed.")
        st.stop()

    with st.spinner("Extracting economic insights from warehouse..."):
        try:
            df_result = fetch_aggregated_econ_data(
                _conn=conn,
                activities=all_activities,
                pollutant=air_pollutant,
                start_year=min(years_selected),
                end_year=max(years_selected),
                valid_pollutants=valid_pollutants,
            )

            if df_result is None or df_result.empty:
                st.warning("No data available for the selected parameters.")
            else:
                fig = px.line(
                    df_result,
                    x="year",
                    y=air_pollutant,
                    color="economic activity",
                    markers=True,
                    title=f"{air_pollutant} Values by Activity Over Time",
                    labels={
                        air_pollutant: f"{air_pollutant} Concentration",
                        "year": "Year",
                        "economic activity": "Economic Activity",
                    },
                )
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Execution Error: {e}")
