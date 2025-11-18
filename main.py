import streamlit as st

st.set_page_config(page_title="Air Quality Dashboard", layout="wide")

st.title("🌍 Air Quality Data Explorer")
st.markdown("""
Welcome to the **Air Quality Dashboard**.

Use the sidebar to navigate between the different tools:
- **Choropleth Maps**: Explore spatial trends in air pollutants.
- **NEMIT Dashboard**: Analyze pollution data across stations.
- **Economic Activity Graphs**: Visualize pollutant values per economic sector.
""")
