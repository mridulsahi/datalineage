import streamlit as st
import streamlit.components.v1 as components
import openai
import os

st.set_page_config(layout="wide")
st.title("🏦 Barclays-Style Data Lineage Dashboard")

st.markdown("This dashboard visualizes end-to-end data flow and metadata lineage. It integrates with Azure SQL and is GPT-ready.")

search_term = st.text_input("🔍 Search a node or job in the lineage")

if search_term:
    st.success(f"Result for: '{search_term}'")
    if st.button("Generate AI Summary"):
        try:
            openai.api_key = st.secrets["openai_key"]["key"]
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Explain the role of {search_term} in the following data pipeline: raw_customer_data → Clean Job → clean_customer_data → Segment Job → customer_segmentation → Dashboard Publish → marketing_dashboard"}]
            )
            st.info(response["choices"][0]["message"]["content"])
        except:
            st.info(f"Mock summary: '{search_term}' is a core node in the pipeline used to generate customer insights.")

st.markdown("---")
st.subheader("📊 Interactive Lineage Graph")

if os.path.exists("lineage_graph.html"):
    with open("lineage_graph.html", "r") as f:
        components.html(f.read(), height=600, scrolling=True)
else:
    st.error("Lineage graph not found. Please run lineage_graph_generator.py first.")

st.markdown("---")
st.subheader("🧪 Azure SQL Metadata (Mock)")
st.info("In hackathon, this will be connected to live Azure SQL to pull real table names and lineage.")
