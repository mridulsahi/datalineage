# Azure SQL mock (fill in credentials in hackathon)
import pyodbc

def get_metadata():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=yourserver.database.windows.net;'
        'DATABASE=yourdb;UID=youruser;PWD=yourpassword'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES")
    return [row[0] for row in cursor.fetchall()]
