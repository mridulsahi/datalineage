
import pyodbc
import pandas as pd

def fetch_lineage_data(server, database, username, password, table):
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
    )
    conn = pyodbc.connect(conn_str)
    query = f"SELECT * FROM {table}"
    return pd.read_sql(query, conn)
