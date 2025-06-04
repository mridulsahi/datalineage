from datalineagegraph import DataLineageVisualizer
# import openai

import streamlit as st
import pandas as pd
import pyodbc
import openai

import streamlit as st
import pandas as pd
import pyodbc
import openai


# --- Streamlit Page Setup ---
st.set_page_config(page_title="Lineage Dashboard", layout="wide")
st.title(" Data Lineage Dashboard")

# --- Azure SQL Credentials ---
with st.expander("Enter Azure SQL Credentials"):
    server = st.text_input("Server", value="tracelineage.database.windows.net")
    database = st.text_input("Database", value="traceMatesDB")
    username = st.text_input("Username", value="tracematesadmin")
    password = st.text_input("Password", type="password", value="tracemates123$")
    table = st.text_input("Table", value="dbo.datalineage")

# --- Initialize session state for DataFrame ---
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

if st.button("Fetch Data from Azure SQL"):
    try:
        conn_str = f"""
            DRIVER={{SQL Server}};
            SERVER={server};
            DATABASE={database};
            UID={username};
            PWD={password};
        """
        conn = pyodbc.connect(conn_str)
        df = pd.read_sql(f"SELECT * FROM {table}", conn)

        # --- Normalize and Rename Columns ---
        df.columns = [col.lower().strip() for col in df.columns]
        df = df.rename(columns={
            'columnname': 'column',
            'source': 'source',
            'target': 'target',
            'job': 'job'
        })

        # --- Safety Check ---
        required_cols = {"source", "target", "job", "column"}
        missing = required_cols - set(df.columns)
        if missing:
            st.error(f" Missing required columns: {missing}")
            st.stop()

        st.session_state.df = df
        st.success(" Data loaded and processed successfully.")

    except Exception as e:
        st.error(f" Error loading data: {e}")
        st.stop()

# --- Continue only if data is loaded ---
if not st.session_state.df.empty:
    df = st.session_state.df

    st.subheader(" Lineage Data Preview")
    st.dataframe(df.head())

    # --- Search Input ---
    search_term = st.text_input(" Search Node / Job / Column")

    # --- Always define filtered_df safely ---
    filtered_df = df.copy()
    if search_term:
        filtered_df = df[
            df['source'].str.contains(search_term, case=False, na=False) |
            df['target'].str.contains(search_term, case=False, na=False) |
            df['job'].str.contains(search_term, case=False, na=False) |
            df['column'].str.contains(search_term, case=False, na=False)
        ]

    # --- GPT Summary Generation ---
    if st.button(" Generate Summary"):
        if df.empty:
            st.warning(" Please load data before generating a summary.")
        elif not search_term:
            st.warning(" Please enter a search term.")
        elif filtered_df.empty:
            st.warning(" No results found for that search.")
        else:
            sources = ', '.join(filtered_df['source'].dropna().unique())
            targets = ', '.join(filtered_df['target'].dropna().unique())
            jobs = ', '.join(filtered_df['job'].dropna().unique())

            prompt = f"""
Summarize the following data lineage for: {search_term}

**Sources**: {sources}
**Targets**: {targets}
**Jobs**: {jobs}

Detailed Records:
{filtered_df.to_string(index=False)}
            """

            try:
                openai.api_key = "7eae50ec86ab43658d29c353fd6f3aed"
                openai.api_base="https://bh-uk-openai-tracemates.openai.azure.com/"
                openai.api_version="2023-07-01-preview"
                openai.api_type="azure"
                endpoint_url = "https://bh-uk-openai-tracemates.openai.azure.com/"
                response = openai.ChatCompletion.create(
                    engine="gpt-35-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                summary = response['choices'][0]['message']['content']
                st.info(summary)
            except Exception as e:
                st.error(f"GPT Summary failed: {e}")

    # --- Lineage Graph ---
    st.subheader("Lineage Graph")
    try:
        visualizer = DataLineageVisualizer()
        visualizer.load_data(filtered_df)
        fig = visualizer.create_interactive_plot()
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f" Could not generate graph: {e}")
else:
    st.info(" Load data from Azure SQL to begin.")