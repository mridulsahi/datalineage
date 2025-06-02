
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("Data Lineage Dashboard")

search_query = st.text_input("Search for a node:")
if search_query:
    st.success(f"Found lineage path or match for: '{search_query}'")
    if st.button("Generate Summary"):
        st.info("This is a mock summary generated for demo purposes.")

st.markdown("---")
components.html(open("lineage_graph.html", "r").read(), height=600, scrolling=True)
