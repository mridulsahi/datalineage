
import openai
import pandas as pd
import pyodbc

def generate_summary_with_openai(search_term, df, openai_api_key):
    openai.api_key = openai_api_key
    context_df = df[(df["source"].str.contains(search_term, case=False)) | 
                    (df["target"].str.contains(search_term, case=False))]

    if context_df.empty:
        return "No relevant lineage data found."

    sample_data = context_df.to_string(index=False)
    prompt = f"Summarize the data lineage and transformation jobs related to: {search_term}\n\n{sample_data}\n\nSummary:"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error generating summary: {e}"

def fetch_data_from_azure_sql(server, database, username, password, table_name):
    try:
        connection_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};DATABASE={database};UID={username};PWD={password}'
        )
        conn = pyodbc.connect(connection_str)
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        raise RuntimeError(f"Azure SQL Connection Error: {e}")
