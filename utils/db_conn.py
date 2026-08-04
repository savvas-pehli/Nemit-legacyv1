# utils/db.py

import streamlit as st
#from typing import Any
import os 
import duckdb
import pandas as pd
import logging

logger = logging.getLogger(__name__)

@st.cache_resource
def get_db_connection():
    """Returns a cached SQL connection using credentials from Streamlit secrets."""
    token = None
    if "token" in st.secrets['motherduck']:
        creds= st.secrets["motherduck"]
        token=creds['token']
    else:
        token = os.getenv("MOTHERDUCK_TOKEN")

    if not token:
        msg = "CRITICAL: MotherDuck token is missing. Pipeline halted."
        st.error(msg)
        logger.error(msg)
        st.stop()
        
        
    target_database='my_db'
    
    try:
        # Connecting directly to the cloud database using the resolved token
        logger.info(f"Establishing cloud connection to MotherDuck database: {target_database}")
        conn = duckdb.connect(f'md:{target_database}?motherduck_token={token}')
        return conn
    except Exception as e:
        logger.critical(f"Cloud Connection Failed on DB {target_database}: {str(e)}", exc_info=True)
        st.error(f"Cloud Connection Failed: {e}")
        st.stop()

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


def fetch_query(conn, query: str, params: tuple | list | None = None) -> pd.DataFrame | None:
    """
    Executes a SQL query against MotherDuck and returns a Pandas DataFrame.
    Supports secure parameter binding for dynamic WHERE clauses.
    DuckDB handles this conversion natively and highly efficiently.
    """
    try:
        # If parameters are provided, pass them to the execution engine
        if params:
            return conn.execute(query, params).df()
        
        # Fallback for static queries without parameters
        return conn.execute(query).df()
        
    except Exception as e:
        st.error(f"Query Execution Error: {e}")
        return None


