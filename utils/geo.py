import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry.polygon import orient
from shapely.ops import transform
import streamlit as st

def enforce_multipolygon_orientation(geom):
    """Forces the Right-Hand Rule (Counter-Clockwise) for WebGL."""
    if geom.geom_type == 'Polygon':
        return orient(geom, sign=1.0)
    elif geom.geom_type == 'MultiPolygon':
        from shapely.geometry import MultiPolygon
        return MultiPolygon([orient(p, sign=1.0) for p in geom.geoms])
    return geom

def heal_coordinate_inversion(geom):
    """
    Detects if coordinates were stored as [Lat, Lon] instead of [Lon, Lat]
    and mathematically inverts the matrix.
    """
    if geom is None or geom.is_empty:
        return geom
        
    # Extract a single sample point from the geometry
    sample_x = geom.representative_point().x
    
    # Greece's Longitude (X) is ~20 to 28. Latitude (Y) is ~34 to 41.
    # If X is over 30, the database illegally stored Latitude first.
    if sample_x > 30:
        # Swap every (X, Y) coordinate pair to (Y, X)
        return transform(lambda x, y, z=None: (y, x), geom)
        
    return geom

@st.cache_data(show_spinner=False)
def load_geo_original_data(geodata: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    The ultimate spatial healing pipeline.
    Parses WKT, inverts corrupt axes, enforces CRS, heals topology, and sets WebGL winding.
    """
    if geodata is None or geodata.empty:
        return gpd.GeoDataFrame()

    # 1. Parse WKT from the database WKT strings
    geodata['geometry'] = geodata['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(geodata, geometry='geometry')
    
    # 2. INVERSION FIX: Correct the Coordinate Matrix before Mapbox reads it
    gdf['geometry'] = gdf['geometry'].apply(heal_coordinate_inversion)
    
    # 3. Strict Mapbox EPSG:4326 Projection
    gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
    
    # 4. Heal Microscopic Topology Collisions
    gdf['geometry'] = gdf['geometry'].buffer(0)
    
    # 5. Enforce Right-Hand Rule (Prevents Back-Face Culling)
    gdf['geometry'] = gdf['geometry'].apply(enforce_multipolygon_orientation)
    
    # 6. Decimate for Browser WebGL limits
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.002, preserve_topology=True)
    
    return gdf[~gdf.is_empty]
