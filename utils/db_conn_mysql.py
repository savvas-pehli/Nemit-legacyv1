import streamlit as st
import pandas as pd
from sqlalchemy import text

@st.cache_resource
def get_db_connection():
    """
    Returns a cached SQL connection using credentials from Streamlit secrets.
    Requires a [connections.mysql] block in .streamlit/secrets.toml.
    """
    try:
        # Streamlit natively handles SQLAlchemy connections via st.connection
        # This automatically maps to the [connections.mysql] section in secrets.toml
        creds = st.secrets["connections.mysql"]
        db_url = f"mysql://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
        conn = st.connection("connections.mysql", type="sql",url=db_url)
        return conn
    except Exception as e:
        st.error(f"CRITICAL: MySQL Connection Failed. Ensure PyMySQL is installed and secrets.toml is configured. Error: {e}")
        st.stop()

def quote(value: str) -> str:
    """Wraps a string safely for SQL usage."""
    return f"'{value}'"

def format_in_clause(values: list[str]) -> str:
    """Formats a list of values into a SQL-safe IN clause."""
    if not values:
        return "()"
    return f"({', '.join(quote(v) for v in values)})"

def fetch_query(conn, query: str, params: dict = None) -> pd.DataFrame | None:
    """
    Executes a SQL query against MySQL and returns a Pandas DataFrame.
    Supports parameterized queries (params) to prevent SQL Injection.
    """
    try:
        # If parameters are provided, execute safely with binding
        if params:
            # Streamlit's conn.query returns a pandas DataFrame natively
            return conn.query(query, params=params)
        else:
            return conn.query(query)
    except Exception as e:
        st.error(f"Query Execution Error: {e}")
        return None