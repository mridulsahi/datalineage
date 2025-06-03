import streamlit as st
import pandas as pd
from utils.sql_connector import fetch_data_from_azure_sql
from utils.summary_generator import generate_openai_summary
from datetime import datetime
import plotly.graph_objects as go
import networkx as nx

st.set_page_config(page_title="Lineage Dashboard", layout="wide")
st.title("Data Lineage Dashboard ")

# --- Data source selection ---
data_source = st.radio("Select Data Source", ["CSV Upload", "Azure SQL"], horizontal=True)

# --- Load Data ---
if data_source == "CSV Upload":
    uploaded_file = st.file_uploader("Upload a lineage CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
    else:
        st.warning("Upload a CSV file to continue.")
        st.stop()
else:
    st.subheader(" Azure SQL Credentials")
    with st.expander("Enter your Azure SQL credentials"):
        server = st.text_input("Server", value="your-server.database.windows.net")
        database = st.text_input("Database", value="your-db")
        username = st.text_input("Username", value="your-username")
        password = st.text_input("Password", type="password")

    if st.button("Fetch Data from Azure SQL"):
        try:
            df = fetch_data_from_azure_sql(server, database, username, password)
            st.success("Data loaded successfully from Azure SQL.")
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
            st.stop()
    else:
        st.stop()

# --- Preview Data ---
st.subheader("Lineage Data Preview")
st.dataframe(df.head())

# --- Search and Summary ---
search_term = st.text_input("Search Node / Job")
if search_term:
    st.success(f"Search Result for: {search_term}")
    if st.button("Generate Summary (GPT)"):
        summary = generate_openai_summary(search_term)
        st.info(summary)

# --- Graph: Simple Node Graph from source/target ---
st.subheader("Lineage Graph")
try:
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(row["source"], row["target"], job=row.get("job", "N/A"))

    pos = nx.spring_layout(G, seed=42)
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=1, color="#888"),
        hoverinfo='none',
        mode='lines')

    node_trace = go.Scatter(
        x=[], y=[], text=[], mode='markers+text',
        marker=dict(size=20, color='skyblue', line_width=2),
        textposition="bottom center"
    )

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace['x'] += [x0, x1, None]
        edge_trace['y'] += [y0, y1, None]

    for node in G.nodes():
        x, y = pos[node]
        node_trace['x'] += [x]
        node_trace['y'] += [y]
        node_trace['text'] += [node]

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=20, r=20, t=40),
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False))
                    )
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Could not generate graph: {e}")
