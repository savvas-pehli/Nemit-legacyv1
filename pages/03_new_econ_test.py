import streamlit as st
import numpy as np
import plotly.express as px
from utils.db_conn import get_db_connection, fetch_query,format_in_clause
from queries.sql_queries import (AIR_POL_QUERY,
                              MAIN_ECON_ACTIVITY,
                              SUB_ECON_QUERY,
                              ECON_ACTIVITY_QUERY)

# Page setup
st.set_page_config(layout="wide",page_title="Economic activity Pollution Data Dashboard", page_icon="📈")

st.markdown("# Economic activity Pollution Data Dashboard")
st.sidebar.header("Plotting Demo")

# Database connection
conn=get_db_connection()
st.sidebar.title('Time and gas filters')

# Always show year slider
year_query = """SELECT DISTINCT(Year) as Year FROM gas_econ_activity;"""
year_df = fetch_query(conn, year_query)
if year_df is not None and not year_df.empty:
    year_list = list(year_df["Year"])
    years_selected = st.sidebar.select_slider(
        'Choose year range', 
        options=np.sort(year_list), 
        value=(min(year_list), max(year_list))
    )
else:
    st.error("Failed to load years from database.")
    st.stop()
    

# Always show air pollutant selector
air_pol_list=fetch_query(conn, AIR_POL_QUERY)
air_pollutant = st.sidebar.selectbox('Please select one air pollutant', options=list(air_pol_list['column_name']))

# Main economic activity selection
econ_activity_list=fetch_query(conn,MAIN_ECON_ACTIVITY)
econ_act = st.multiselect('Please select economic activity', options=np.sort(list(econ_activity_list['economic activity'])), max_selections=5)

# Info and checkbox logic
st.markdown('In case you want to further investigate the aspects of each main economic activity, please check the checkbox in order to activate the selection of sub-economic activities.')

enable_sub_selection = False
sub_econ_act = []

if len(econ_act) == 1:
    enable_sub_selection = st.checkbox('Enable sub-economic activity selection (up to 5)', value=False)

    if enable_sub_selection:
        code_name = list(econ_activity_list[econ_activity_list['economic activity'].isin(econ_act)]['code name'])
        code_name_regex = f"{'|'.join(code_name)}"
        sub_econ_query=SUB_ECON_QUERY.format(code_name_regex=code_name_regex)
        sub_list = fetch_query(conn,sub_econ_query)
        sub_econ_act = st.multiselect(
            'Please select sub-economic activities',
            options=np.sort(list(sub_list['economic activity'])),
            max_selections=5
        )

elif len(econ_act) > 1:
    st.markdown("ℹ️ Please select only **one** main economic activity to enable sub-economic activity selection.")

# Final list of activities
all_activities = econ_act + sub_econ_act
econ_act_query = format_in_clause(all_activities) if all_activities else None
# Button to trigger query
run_query = st.button("Run Query")
# Only run query if required inputs are present
if run_query:
    if not econ_act:
        st.warning("Please select at least one economic activity.")
    elif not air_pollutant:
        st.warning("Please select an air pollutant.")
    else:
        data_query=ECON_ACTIVITY_QUERY.format(air_pollutant=air_pollutant,econ_act_query=econ_act_query,start=min(years_selected),end=max(years_selected))
        filtered_df = fetch_query(conn,data_query)

        if filtered_df.empty or filtered_df is None:
            st.warning("No data available for the selected options.")
        else:
            fig = px.line(
                filtered_df,
                x="year",
                y=air_pollutant,
                color="economic activity",
                markers=True,
                title=f"{air_pollutant} Values by Activity Over Years",
                labels={
                    air_pollutant: f"{air_pollutant} Value",
                    "year": "Year",
                    "economic activity": "Economic Activity"
                },
            )
            st.plotly_chart(fig, use_container_width=True)
