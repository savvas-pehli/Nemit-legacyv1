import calendar

import pandas as pd
import streamlit as st
from services.npets_service import (
    fetch_aggregated_npets_data,
    fetch_temporal_metadata,
    get_npets_schema,
)
from utils.constants import (
    ISODOW_MAP_0_INDEXED,
    NPETS_PLACE_MAPPING,
    NPETS_PLACES,
    NPETS_REVERSE_PLACE_MAPPING,
    NPETS_SEASONS,
    NPETS_TIMEFRAMES,
    NPETS_TOOLS,
)
from utils.db_conn import get_database_engine
from utils.plotting import plot_particle_distribution

st.set_page_config(layout="wide", page_title="nPETS Particle Analysis")
st.markdown("## ⚙️ nPETS Particle Distribution Analysis")
st.markdown("---")

conn = get_database_engine()

# ==============================================================================
# 1. PRIMARY FILTERS
# ==============================================================================
st.markdown("### Base Filters")
col1, col2, col3 = st.columns(3)

selected_tool = st.sidebar.selectbox("Select Tool Engine:", options=NPETS_TOOLS)
selected_places = st.sidebar.multiselect(
    "Select Place (Max 2):",
    options=NPETS_PLACES,
    default=[NPETS_PLACES[0]],
    max_selections=2,
)
selected_seasons = st.sidebar.multiselect(
    "Select Season(s):", options=NPETS_SEASONS, default=NPETS_SEASONS
)

if not selected_places or not selected_seasons:
    st.warning("⚠️ Please select at least one Place and one Season.")
    st.stop()

# ==============================================================================
# 2. DYNAMIC MEASUREMENT RETRIEVAL
# ==============================================================================
try:
    available_columns = get_npets_schema(conn, selected_tool)
except Exception as e:
    st.error(f"Failed to retrieve schema: {e}")
    st.stop()

st.markdown("### Measurement Selection")
if available_columns:
    selected_measurements = st.multiselect(
        "Select Particle Bins to Analyze:",
        options=available_columns,
        default=available_columns[:2]
        if len(available_columns) >= 2
        else available_columns,
        max_selections=2,
    )
else:
    st.error(f"No measurement columns found for {selected_tool}.")
    st.stop()

if not selected_measurements:
    st.warning("⚠️ You must select at least one measurement bin.")
    st.stop()

# ==============================================================================
# 3. AGGREGATION & EXECUTION
# ==============================================================================
st.markdown("### Time Aggregation")
selected_timeframe = st.radio(
    "Select Time Resolution:", options=NPETS_TIMEFRAMES, horizontal=True
)
selected_agg_type = st.radio(
    "Select Aggregation:", options=["Mean", "Median"], horizontal=True
)

# Map UI strings to database strings securely
db_places = [NPETS_PLACE_MAPPING[p] for p in selected_places]

if st.button("Execute Analysis", type="primary"):
    with st.spinner("Executing analytical join..."):
        try:
            df_result = fetch_aggregated_npets_data(
                _conn=conn,
                agg_type=selected_agg_type,
                tool_name=selected_tool,
                places=db_places,
                seasons=selected_seasons,
                measurements=selected_measurements,
                timeframe=selected_timeframe,
            )
            if df_result.empty:
                st.warning("No data found for the selected parameters.")
                st.stop()

            meta = fetch_temporal_metadata(
                _conn=conn,
                tool_name=selected_tool,
                places=db_places,
                seasons=selected_seasons,
            )

            # Map database locations back to UI names
            df_result["location"] = df_result["location"].map(
                NPETS_REVERSE_PLACE_MAPPING
            )

            if selected_timeframe == "Day":
                df_result["time_bucket"] = df_result["time_bucket"].map(
                    ISODOW_MAP_0_INDEXED
                )
                df_result["time_bucket"] = pd.Categorical(
                    df_result["time_bucket"],
                    categories=list(ISODOW_MAP_0_INDEXED.values()),
                    ordered=True,
                )

            df_result.rename(columns={"time_bucket": selected_timeframe}, inplace=True)
            df_result.dropna(how="all", inplace=True)

            years_str = ", ".join(map(str, meta["years"]))
            months_str = ", ".join([calendar.month_abbr[m] for m in meta["months"]])

            st.success(
                f"📊 **Contextual Temporal Footprint:** Diurnal/weekly averages derived from **Years {years_str}** across **Months {months_str}**."
            )

            fig = plot_particle_distribution(
                df_result, selected_measurements, selected_timeframe
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Execution Error: {e}")
