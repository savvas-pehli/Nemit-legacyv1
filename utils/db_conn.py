# utils/db.py

import streamlit as st
#from typing import Any
import pandas as pd
import logging
from sqlalchemy import create_engine, text
logger = logging.getLogger(__name__)

@st.cache_resource
def get_database_engine():
    """
    Initializes a production-grade connection pool.
    This runs exactly once and is shared across all Streamlit sessions.
    """
    # 1. Fetch credentials securely from Streamlit secrets
    db_config = st.secrets["connections"]["postgresql_docker"]
    
    # 2. Construct the connection string dynamically
    db_url = f"{db_config['dialect']}+{db_config['driver']}://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    # 3. Create the Engine with production safety guards
    engine = create_engine(
        db_url,
        pool_size=5,          # Keep 5 connections permanently open
        max_overflow=10,      # Allow up to 10 extra connections during traffic spikes
        pool_pre_ping=True,   # Pings the DB before every query to ensure the connection hasn't died
        pool_recycle=3600     # Refresh connections every hour to prevent silent timeouts
    )
    
    return engine

def quote(value: str) -> str:
    """Wraps a string safely for SQL usage."""
    return f"'{value}'"

def format_in_clause(values: list[str]) -> str:
    """Formats a list of values into a SQL-safe IN clause."""
    if not values:
        return "()"
    # DuckDB/PostgreSQL strictly requires single quotes for strings
    return f"({', '.join(quote(v) for v in values)})"

def column_name_transform(values:list[str])-> list:
    if not values:
        return "()"
    # DuckDB/PostgreSQL strictly requires single quotes for strings
    return f"({', '.join(quote(v) for v in values)})"


def fetch_query(conn, query: str, params: dict | None = None) -> pd.DataFrame | None:
    """
    Executes a SQL query against PostgreSQL using bulletproof named parameters.
    """
    try:
        if params is not None:
            # Wrap the string to enable named parameter binding (e.g., :param_name)
            query = text(query)
            
        return pd.read_sql(query, con=conn, params=params)
    except Exception as e:
        st.error(f"Query Execution Error: {e}")
        return None


