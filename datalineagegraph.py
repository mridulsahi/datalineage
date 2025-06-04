import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
import math
from collections import deque

class DataLineageVisualizer:
    def __init__(self):
        self.df = None
        self.graph = nx.DiGraph()
        self.node_levels = {}

    def load_data(self, data):
        if isinstance(data, str):
            self.df = pd.read_csv(data)
        else:
            self.df = data.copy()

        self.df = self.df.dropna()
        self.df.columns = [col.lower() for col in self.df.columns]
        self.df['source'] = self.df['source'].astype(str).str.strip()
        self.df['target'] = self.df['target'].astype(str).str.strip()
        self.df['column'] = self.df['column'].astype(str).str.strip()
        self.df['job'] = self.df['job'].astype(str).str.strip()
        return self.df

    def build_graph(self, filtered_df=None):
        df_to_use = filtered_df if filtered_df is not None else self.df
        self.graph.clear()
        for _, row in df_to_use.iterrows():
            s, t, col, job = row['source'], row['target'], row['column'], row['job']
            self.graph.add_node(s)
            self.graph.add_node(t)
            self.graph.add_edge(s, t, column=col, job=job)
        self._calculate_node_levels()

    def _calculate_node_levels(self):
        try:
            levels = list(nx.topological_generations(self.graph))
            for idx, level in enumerate(levels):
                for node in level:
                    self.node_levels[node] = idx
        except:
            self._calculate_levels_with_cycles()

    def _calculate_levels_with_cycles(self):
        self.node_levels = {}
        roots = [n for n in self.graph.nodes if self.graph.in_degree(n) == 0]
        if not roots:
            min_in = min(dict(self.graph.in_degree()).values())
            roots = [n for n in self.graph.nodes if self.graph.in_degree(n) == min_in]

        q = deque([(n, 0) for n in roots])
        visited = {}

        while q:
            node, level = q.popleft()
            if node not in visited or level > visited[node]:
                visited[node] = level
                for succ in self.graph.successors(node):
                    q.append((succ, level + 1))
        self.node_levels = visited

    def _create_layout(self):
        levels = {}
        for node, level in self.node_levels.items():
            levels.setdefault(level, []).append(node)

        pos = {}
        x_gap, y_gap = 3.0, 2.0

        for lvl, nodes in levels.items():
            x = lvl * x_gap
            y_start = (len(nodes) - 1) * y_gap / 2
            for i, node in enumerate(sorted(nodes)):
                pos[node] = (x, y_start - i * y_gap)
        return pos

    def create_interactive_plot(self, filtered_df=None):
        self.build_graph(filtered_df)
        if not self.graph.nodes:
            return go.Figure().add_annotation(text="No data", x=0.5, y=0.5, showarrow=False)

        pos = self._create_layout()
        fig = go.Figure()

        node_color = "#1f77b4"
        for node in self.graph.nodes:
            x, y = pos[node]

            # Draw rectangle for the node
            fig.add_shape(type="rect", x0=x-0.8, y0=y-0.4, x1=x+0.8, y1=y+0.4,
                          fillcolor=node_color, line=dict(color="white"))

            # Draw label above the rectangle
            fig.add_trace(go.Scatter(
                x=[x],
                y=[y + 0.5],  # label positioned slightly above box
                mode='text',
                text=[node],
                textposition="top center",
                textfont=dict(size=12, color="black"),
                hoverinfo='skip',
                showlegend=False
            ))

        edge_colors = px.colors.qualitative.Set3
        job_list = list(self.df['job'].unique())
        job_color_map = {job: edge_colors[i % len(edge_colors)] for i, job in enumerate(job_list)}

        for u, v, data in self.graph.edges(data=True):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            fig.add_trace(go.Scatter(
                x=[x0 + 0.8, x1 - 0.8, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=2, color=job_color_map.get(data["job"], "#ccc")),
                hoverinfo='text',
                name=f"{data['job']}"
            ))

        fig.update_layout(
            title="Data Lineage Diagram",
            showlegend=True,
            hovermode='closest',
            margin=dict(b=40, l=20, r=20, t=60),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=700
        )
        return fig
