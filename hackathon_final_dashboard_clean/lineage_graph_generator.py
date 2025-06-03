from pyvis.network import Network

net = Network(height="600px", width="100%", directed=True)

net.add_node("raw_customer_data", label="raw_customer_data\n[DB]", title="Azure SQL DB", color="blue", shape="box", href="https://example.com/raw_customer_data", physics=True)
net.add_node("Clean Job", label="Clean Job\n[ETL]", color="gray", shape="box", title="Transformation", physics=True)
net.add_node("clean_customer_data", label="clean_customer_data\n[Dataset]", color="orange", shape="box", href="https://example.com/clean_customer_data", title="Processed data", physics=True)
net.add_node("Segment Job", label="Segment Job\n[ETL]", color="gray", shape="box", title="Segmentation", physics=True)
net.add_node("customer_segmentation", label="customer_segmentation\n[Dataset]", color="orange", shape="box", href="https://example.com/customer_segmentation", title="Segmentation output", physics=True)
net.add_node("Dashboard Publish", label="Dashboard Publish\n[BI]", color="purple", shape="box", title="Publishing", physics=True)
net.add_node("marketing_dashboard", label="marketing_dashboard\n[BI Tool]", color="purple", shape="box", href="https://example.com/dashboard", title="Dashboard", physics=True)

edges = [
    ("raw_customer_data", "Clean Job"),
    ("Clean Job", "clean_customer_data"),
    ("clean_customer_data", "Segment Job"),
    ("Segment Job", "customer_segmentation"),
    ("customer_segmentation", "Dashboard Publish"),
    ("Dashboard Publish", "marketing_dashboard")
]
for src, tgt in edges:
    net.add_edge(src, tgt)

net.set_options("""
var options = {
  "nodes": {"borderWidth": 1, "shadow": true},
  "edges": {"arrows": {"to": {"enabled": true}}, "smooth": true},
  "physics": {"enabled": true, "stabilization": {"iterations": 100}}
}
""")

net.show("lineage_graph.html")
