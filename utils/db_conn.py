# utils/db.py

import streamlit as st
#from typing import Any
import os 
import duckdb
import pandas as pd
@st.cache_resource
def get_db_connection():
    """Returns a cached SQL connection using credentials from Streamlit secrets."""
    token = None
    print(st.secrets)
    if "token" in st.secrets['motherduck']:
        creds= st.secrets["motherduck"]
        token=creds['token']
        print(token)
    else:
        token = os.getenv("MOTHERDUCK_TOKEN")
        print(token)

    if not token:
        st.error("CRITICAL: MotherDuck token is missing. Pipeline halted.")
        st.stop()
        
    target_database='my_db'
    
    try:
        # Connecting directly to the cloud database using the resolved token
        conn = duckdb.connect(f'md:{target_database}?motherduck_token={token}')
        return conn
    except Exception as e:
        st.error(f"Cloud Connection Failed: {e}")
        st.stop()
        
    #creds = st.secrets["motherduck"]
    #token=creds["token"]
    #db_url = f"mysql://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    #db_url = f"mysql://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    #return st.connection("mysql", type="sql", url=db_url)

def quote(value: str) -> str:
    """Wraps a string safely for SQL usage."""
    return f"'{value}'"

#def format_in_clause(values: list[str]) -> str:
#    """Formats a list of values into a SQL-safe IN clause."""
#    if not values:
#        return "()"
#    return f"({', '.join(quote(v) for v in values)})" if values else "()"
#
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

def fetch_query(conn, query: str) -> pd.DataFrame | None:
    """
    Executes a SQL query against MotherDuck and returns a Pandas DataFrame.
    DuckDB handles this conversion natively and highly efficiently.
    """
    try:
        # DuckDB's .df() method natively outputs to Pandas
        return conn.execute(query).df()
    except Exception as e:
        st.error(f"Query Execution Error: {e}")
        return None
#def fetch_query(conn, query: str) -> Any:
#    """Executes an SQL query safely with basic error handling."""
#    try:
#        return conn.query(query)
#    except Exception as e:
#        st.error(f"Query execution Error: {e}")
#        return None
