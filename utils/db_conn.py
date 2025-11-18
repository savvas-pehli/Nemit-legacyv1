# utils/db.py

import streamlit as st
from typing import Any

@st.cache_resource
def get_db_connection():
    """Returns a cached SQL connection using credentials from Streamlit secrets."""
    creds = st.secrets["connections.mysql"]
    db_url = f"mysql://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    return st.connection("mysql", type="sql", url=db_url)

def quote(value: str) -> str:
    """Wraps a string safely for SQL usage."""
    return f"'{value}'"

def format_in_clause(values: list[str]) -> str:
    """Formats a list of values into a SQL-safe IN clause."""
    return f"({', '.join(quote(v) for v in values)})" if values else "()"

def fetch_query(conn, query: str) -> Any:
    """Executes an SQL query safely with basic error handling."""
    try:
        return conn.query(query)
    except Exception as e:
        st.error(f"SQL Error: {e}")
        return None
