import streamlit as st
import pyodbc  # Used to connect to Azure SQL
import openai  # Will be used for GPT summary (mocked here)

st.set_page_config(layout="wide")
st.title("Azure SQL + OpenAI Lineage Dashboard")

# Search bar
search_term = st.text_input("🔍 Search for a table or transformation job")

# If something is searched
if search_term:
    st.success(f"Results for: '{search_term}'")

    # Button to generate AI summary
    if st.button("Generate AI Summary"):
        # GPT would go here - for now, we mock it
        summary = f"'{search_term}' is a critical component in the customer pipeline and is linked to downstream analytics."
        st.info(f"Mock GPT Summary: {summary}")

# Try Azure SQL connection (fallback to mock if fails)
st.markdown("---")
st.subheader("📊 Sample Data from Azure SQL")

try:
    # Replace with your actual credentials
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=your_server.database.windows.net;'
        'DATABASE=your_db_name;'
        'UID=your_user;'
        'PWD=your_password'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 5 * FROM your_table")
    rows = cursor.fetchall()

    # Extract columns
    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, row)) for row in rows]

    st.dataframe(data)

except Exception as e:
    st.warning("Could not connect to Azure SQL. Using mock data.")
    st.dataframe([
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"}
    ])
