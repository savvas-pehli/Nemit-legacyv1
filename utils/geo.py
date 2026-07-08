import pandas as pd
import geopandas as gpd 
from shapely import wkt
import streamlit as st

@st.cache_data(show_spinner=False)
def load_geo_original_data(geodata:pd.DataFrame,):
    """Loads GeoJSON geometries from a CSV based on region name."""

    geodata['geometry'] = geodata['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(geodata, geometry='geometry', crs="EPSG:4326")
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.005, preserve_topology=True)
    geojson = gdf.set_index("Municipality").__geo_interface__
    
    return geojson
