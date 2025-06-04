
import pyodbc
import pandas as pd
import os

def fetch_lineage_data(server, database, username, password, table):
    #conn_str = pyodbc.connect(os.getenv("traceMatesDB"))
    #conn_str="Driver={ODBC Driver 18 for SQL Server};Server=tcp:tracelineage.database.windows.net,1433;Database=traceMatesDB;Uid=tracemates;Pwd=tracemates123$;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;Authentication=ActiveDirectoryPassword"
    # #print(conn_str)
    # conn_str = (
    #     f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    #     f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
    # )
    conn_str = (
    "DRIVER={SQL Server};"
    "SERVER=tracelineage.database.windows.net;"
    "DATABASE=traceMatesDB;"
    "UID=tracematesadmin;"
    "PWD=tracemates123$;"
    )
    conn = pyodbc.connect(conn_str)
    print(conn_str)

    #conn = pyodbc.connect(conn_str)
    query = f"SELECT * FROM {table}"
    return pd.read_sql(query, conn_str)




