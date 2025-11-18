import pandas as pd
import geopandas as gpd 
from shapely import wkt
from functools import lru_cache
import streamlit as st
from utils.translation_helper import greek_to_latin

#lru_cache(maxsize=32)
@st.cache_data(show_spinner=False)
def load_geo_original_data(region: str,need_ids):
    """Loads GeoJSON geometries from a CSV based on region name."""
    region = region.replace(" ", "_")
    url = f'https://raw.githubusercontent.com/savvas-pehli/gas_app/refs/heads/main/{region}_municipalities_geometries.csv'
    geodata = pd.read_csv(url)
    municipal_filter=map(greek_to_latin,need_ids)
    geodata['geometry'] = geodata['geometry'].apply(wkt.loads)
    geodata = geodata[geodata['Municipality'].isin(municipal_filter)]
    gdf = gpd.GeoDataFrame(geodata, geometry='geometry', crs="EPSG:4326")
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    geojson = gdf.set_index("Municipality").__geo_interface__
    
    return geojson