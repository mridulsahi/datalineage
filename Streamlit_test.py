import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime
import numpy as np
import math

# Set page config
st.set_page_config(
    page_title="Data Lineage Viewer",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .filter-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class DataLineageVisualizer:
    def __init__(self):
        self.df = None
        self.graph = nx.DiGraph()
        self.pos = None
        self.node_levels = {}
        
    def load_data(self, data):
        """Load and process the lineage data"""
        if isinstance(data, str):
            self.df = pd.read_csv(data)
        else:
            self.df = data.copy()
        
        # Clean the data
        self.df = self.df.dropna()
        self.df['source'] = self.df['source'].astype(str).str.strip()
        self.df['target'] = self.df['target'].astype(str).str.strip()
        self.df['column'] = self.df['column'].astype(str).str.strip()
        self.df['job'] = self.df['job'].astype(str).str.strip()
        
        return self.df
    
    def build_graph(self, filtered_df=None):
        """Build NetworkX graph from the data"""
        df_to_use = filtered_df if filtered_df is not None else self.df
        
        self.graph.clear()
        
        # Add nodes and edges
        for _, row in df_to_use.iterrows():
            source, target, column, job = row['source'], row['target'], row['column'], row['job']
            
            # Add nodes with attributes
            if source not in self.graph:
                self.graph.add_node(source, node_type='table')
            if target not in self.graph:
                self.graph.add_node(target, node_type='table')
            
            # Add edge with attributes
            self.graph.add_edge(source, target, column=column, job=job, weight=1)
        
        # Calculate node levels for better layout
        self._calculate_node_levels()
        
    def _calculate_node_levels(self):
        """Calculate hierarchical levels for nodes using topological sorting"""
        # Find strongly connected components and create condensation graph
        try:
            # Use topological generations for DAG-like structure
            levels = list(nx.topological_generations(self.graph))
            self.node_levels = {}
            
            for level_idx, level_nodes in enumerate(levels):
                for node in level_nodes:
                    self.node_levels[node] = level_idx
                    
        except nx.NetworkXError:
            # If graph has cycles, use a different approach
            self._calculate_levels_with_cycles()
    
    def _calculate_levels_with_cycles(self):
        """Handle graphs with cycles by using longest path approach"""
        self.node_levels = {}
        
        # Find root nodes (no incoming edges)
        root_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        
        if not root_nodes:
            # If no root nodes, pick nodes with minimum in-degree
            min_in_degree = min(self.graph.in_degree(n) for n in self.graph.nodes())
            root_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == min_in_degree]
        
        # BFS-like approach to assign levels
        from collections import deque
        queue = deque([(node, 0) for node in root_nodes])
        visited = {}
        
        while queue:
            node, level = queue.popleft()
            
            # Only update if we found a longer path
            if node not in visited or visited[node] < level:
                visited[node] = level
                
                # Add successors
                for successor in self.graph.successors(node):
                    queue.append((successor, level + 1))
        
        self.node_levels = visited
    
    def create_interactive_plot(self, filtered_df=None):
        """Create interactive plotly visualization with structured data blocks"""
        self.build_graph(filtered_df)
        
        if len(self.graph.nodes()) == 0:
            return go.Figure().add_annotation(
                text="No data to display with current filters",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
        
        # Create structured layout
        pos = self._create_structured_layout()
        
        # Create figure with structured blocks
        fig = go.Figure()
        
        # Add rectangular blocks for tables
        self._add_table_blocks(fig, pos, filtered_df)
        
        # Add connection lines
        self._add_connection_lines(fig, pos, filtered_df)
        
        # Add job labels
        self._add_job_labels(fig, pos, filtered_df)
        
        # Update layout for structured appearance
        fig.update_layout(
            title=dict(
                text="<b>Data Lineage Structure</b>",
                x=0.5,
                font=dict(size=24, color="#2c3e50", family="Arial")
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            ),
            hovermode='closest',
            margin=dict(b=60, l=60, r=60, t=100),
            annotations=[
                dict(
                    text="💡 Hover over blocks for details | Click legend to toggle job visibility",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=-0.08,
                    xanchor='center', yanchor='bottom',
                    font=dict(size=12, color="#7f8c8d")
                )
            ],
            xaxis=dict(
                showgrid=True, 
                gridcolor='rgba(200,200,200,0.3)',
                zeroline=False, 
                showticklabels=False,
                title="Data Flow Direction →"
            ),
            yaxis=dict(
                showgrid=True, 
                gridcolor='rgba(200,200,200,0.3)',
                zeroline=False, 
                showticklabels=False,
                title="System Layers"
            ),
            plot_bgcolor='#fafafa',
            height=800,
            width=1400
        )
        
        return fig
    
    def _create_structured_layout(self):
        """Create a structured layout like a proper data architecture diagram"""
        if not self.node_levels:
            return {}
        
        # Group nodes by level
        levels = {}
        for node, level in self.node_levels.items():
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
        
        pos = {}
        
        # Layout parameters
        level_spacing = 3.0  # Horizontal spacing between levels
        node_spacing = 2.0   # Vertical spacing between nodes
        
        max_level = max(levels.keys()) if levels else 0
        
        for level, nodes in levels.items():
            # Calculate positions for nodes at this level
            x = level * level_spacing
            
            # Sort nodes for consistent positioning
            sorted_nodes = sorted(nodes)
            n_nodes = len(sorted_nodes)
            
            if n_nodes == 1:
                y_positions = [0]
            else:
                # Distribute nodes evenly
                total_height = (n_nodes - 1) * node_spacing
                y_start = total_height / 2
                y_positions = [y_start - i * node_spacing for i in range(n_nodes)]
            
            for i, node in enumerate(sorted_nodes):
                pos[node] = (x, y_positions[i])
        
        return pos
    
    def _add_table_blocks(self, fig, pos, filtered_df):
        """Add rectangular blocks representing tables"""
        # Color scheme for different table types
        color_scheme = {
            'source_system': '#e74c3c',      # Red for source systems
            'raw_data': '#3498db',           # Blue for raw data
            'dimension': '#2ecc71',          # Green for dimensions
            'fact': '#f39c12',               # Orange for facts
            'reporting': '#9b59b6',          # Purple for reporting
            'access': '#1abc9c',             # Teal for access layer
            'default': '#95a5a6'             # Gray for others
        }
        
        for node in self.graph.nodes():
            if node not in pos:
                continue
                
            x, y = pos[node]
            
            # Determine color based on node name
            color = self._get_node_color(node, color_scheme)
            
            # Get node statistics
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            
            # Get associated columns and jobs
            columns = set()
            jobs = set()
            
            # Incoming edges
            for source, target, data in self.graph.in_edges(node, data=True):
                columns.add(data.get('column', ''))
                jobs.add(data.get('job', ''))
            
            # Outgoing edges
            for source, target, data in self.graph.out_edges(node, data=True):
                columns.add(data.get('column', ''))
                jobs.add(data.get('job', ''))
            
            # Create hover text
            hover_text = self._create_node_hover_text(node, in_degree, out_degree, columns, jobs)
            
            # Add rectangular block
            fig.add_shape(
                type="rect",
                x0=x-0.8, y0=y-0.4,
                x1=x+0.8, y1=y+0.4,
                fillcolor=color,
                line=dict(color="white", width=2),
                opacity=0.9
            )
            
            # Add node text
            fig.add_trace(go.Scatter(
                x=[x], y=[y],
                mode='text',
                text=[self._format_node_text(node)],
                textfont=dict(
                    size=11,
                    color='white',
                    family="Arial, sans-serif"
                ),
                textposition="middle center",
                hovertemplate=hover_text + '<extra></extra>',
                showlegend=False,
                name=f"table_{node}"
            ))
    
    def _get_node_color(self, node, color_scheme):
        """Determine node color based on naming patterns"""
        node_lower = node.lower()
        
        if 'core_banking' in node_lower or 'system' in node_lower:
            return color_scheme['source_system']
        elif 'raw' in node_lower:
            return color_scheme['raw_data']
        elif 'dim' in node_lower or 'dimension' in node_lower:
            return color_scheme['dimension']
        elif 'fact' in node_lower:
            return color_scheme['fact']
        elif 'reporting' in node_lower or 'view' in node_lower:
            return color_scheme['reporting']
        elif 'user' in node_lower or 'access' in node_lower:
            return color_scheme['access']
        else:
            return color_scheme['default']
    
    def _format_node_text(self, node):
        """Format node text for display"""
        # Break long names into multiple lines
        if len(node) > 15:
            words = node.replace('_', ' ').split()
            if len(words) > 1:
                mid = len(words) // 2
                line1 = ' '.join(words[:mid])
                line2 = ' '.join(words[mid:])
                return f"{line1}<br>{line2}"
        return node.replace('_', ' ')
    
    def _create_node_hover_text(self, node, in_degree, out_degree, columns, jobs):
        """Create detailed hover text for nodes"""
        columns_text = ', '.join(sorted([c for c in columns if c and c != '*'])) or 'All columns'
        jobs_text = ', '.join(sorted(jobs)) if jobs else 'No jobs'
        
        return (
            f"<b>📊 {node}</b><br>"
            f"<b>Type:</b> Data Table<br>"
            f"<b>Input Connections:</b> {in_degree}<br>"
            f"<b>Output Connections:</b> {out_degree}<br>"
            f"<b>Columns:</b> {columns_text}<br>"
            f"<b>Associated Jobs:</b> {jobs_text}"
        )
    
    def _add_connection_lines(self, fig, pos, filtered_df):
        """Add connection lines between tables"""
        df_to_use = filtered_df if filtered_df is not None else self.df
        
        # Get unique jobs and assign colors
        unique_jobs = sorted(df_to_use['job'].unique())
        colors = px.colors.qualitative.Set3
        job_colors = {job: colors[i % len(colors)] for i, job in enumerate(unique_jobs)}
        
        # Group connections by job
        job_connections = {}
        for _, row in df_to_use.iterrows():
            job = row['job']
            if job not in job_connections:
                job_connections[job] = []
            job_connections[job].append(row)
        
        # Add connection lines for each job
        for job, connections in job_connections.items():
            x_coords, y_coords = [], []
            
            for row in connections:
                source, target = row['source'], row['target']
                
                if source in pos and target in pos:
                    x0, y0 = pos[source]
                    x1, y1 = pos[target]
                    
                    # Create connection line with arrow
                    x_coords.extend([x0 + 0.8, x1 - 0.8, None])
                    y_coords.extend([y0, y1, None])
            
            if x_coords:
                # Add connection line trace
                fig.add_trace(go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode='lines',
                    line=dict(
                        color=job_colors[job],
                        width=3,
                        dash='solid'
                    ),
                    name=f"🔧 {job}",
                    hoverinfo='name',
                    showlegend=True
                ))
                
                # Add arrows
                self._add_arrows(fig, connections, pos, job_colors[job])
    
    def _add_arrows(self, fig, connections, pos, color):
        """Add arrow heads to connection lines"""
        for row in connections:
            source, target = row['source'], row['target']
            
            if source in pos and target in pos:
                x0, y0 = pos[source]
                x1, y1 = pos[target]
                
                # Calculate arrow position
                arrow_size = 0.15
                dx = x1 - x0
                dy = y1 - y0
                length = math.sqrt(dx**2 + dy**2)
                
                if length > 0:
                    # Normalize direction
                    dx, dy = dx/length, dy/length
                    
                    # Arrow tip position (at target edge)
                    tip_x = x1 - 0.8
                    tip_y = y1
                    
                    # Arrow base points
                    base_x1 = tip_x - arrow_size * dx + arrow_size * dy
                    base_y1 = tip_y - arrow_size * dy - arrow_size * dx
                    base_x2 = tip_x - arrow_size * dx - arrow_size * dy
                    base_y2 = tip_y - arrow_size * dy + arrow_size * dx
                    
                    # Add arrow as filled triangle
                    fig.add_trace(go.Scatter(
                        x=[tip_x, base_x1, base_x2, tip_x],
                        y=[tip_y, base_y1, base_y2, tip_y],
                        fill='toself',
                        fillcolor=color,
                        line=dict(color=color, width=0),
                        mode='lines',
                        showlegend=False,
                        hoverinfo='skip'
                    ))
    
    def _add_job_labels(self, fig, pos, filtered_df):
        """Add job labels along connection lines"""
        df_to_use = filtered_df if filtered_df is not None else self.df
        
        for _, row in df_to_use.iterrows():
            source, target, job, column = row['source'], row['target'], row['job'], row['column']
            
            if source in pos and target in pos:
                x0, y0 = pos[source]
                x1, y1 = pos[target]
                
                # Position label at midpoint of connection
                mid_x = (x0 + x1) / 2
                mid_y = (y0 + y1) / 2 + 0.3  # Slightly above the line
                
                # Create label text
                label_text = f"{job}<br>({column})" if column != '*' else job
                
                fig.add_trace(go.Scatter(
                    x=[mid_x],
                    y=[mid_y],
                    mode='text',
                    text=[label_text],
                    textfont=dict(
                        size=9,
                        color='#2c3e50',
                        family="Arial, sans-serif"
                    ),
                    textposition="middle center",
                    showlegend=False,
                    hoverinfo='skip'
                ))
    
    def get_statistics(self, filtered_df=None):
        """Get statistics about the lineage"""
        df_to_use = filtered_df if filtered_df is not None else self.df
        
        stats = {
            'total_tables': len(set(df_to_use['source'].tolist() + df_to_use['target'].tolist())),
            'total_connections': len(df_to_use),
            'total_jobs': df_to_use['job'].nunique(),
            'total_columns': df_to_use['column'].nunique()
        }
        return stats

# Streamlit App
def main():
    st.markdown('<h1 class="main-header">🏗️ Data Architecture Lineage Viewer</h1>', unsafe_allow_html=True)
    
    # Initialize the visualizer
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = DataLineageVisualizer()
    
    df = pd.read_csv("Dummy_data.csv")
    st.session_state.visualizer.load_data(df)
    
    # Sidebar filters
    st.sidebar.markdown('<div class="filter-header">🎛️ Control Panel</div>', unsafe_allow_html=True)
    
    # Job filter
    all_jobs = ['All'] + sorted(df['job'].unique().tolist())
    selected_jobs = st.sidebar.multiselect(
        '🔧 Filter by Jobs',
        options=all_jobs,
        default=['All'],
        help="Select specific ETL jobs to display"
    )
    
    # Table filter
    all_tables = ['All'] + sorted(set(df['source'].tolist() + df['target'].tolist()))
    selected_tables = st.sidebar.multiselect(
        '📊 Filter by Tables',
        options=all_tables,
        default=['All'],
        help="Select specific tables to focus on"
    )
    
    # Column filter
    all_columns = ['All'] + sorted(df['column'].unique().tolist())
    selected_columns = st.sidebar.multiselect(
        '📋 Filter by Columns',
        options=all_columns,
        default=['All'],
        help="Filter by specific column mappings"
    )
    
    # View options
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📐 Display Options**")
    
    show_job_labels = st.sidebar.checkbox("Show Job Labels", value=True, help="Display job names on connections")
    show_column_info = st.sidebar.checkbox("Show Column Info", value=True, help="Include column details in hover")
    
    # Apply filters
    filtered_df = df.copy()
    
    if 'All' not in selected_jobs:
        filtered_df = filtered_df[filtered_df['job'].isin(selected_jobs)]
    
    if 'All' not in selected_tables:
        filtered_df = filtered_df[
            (filtered_df['source'].isin(selected_tables)) | 
            (filtered_df['target'].isin(selected_tables))
        ]
    
    if 'All' not in selected_columns:
        filtered_df = filtered_df[filtered_df['column'].isin(selected_columns)]
    
    # Display statistics
    st.markdown("### 📈 Architecture Overview")
    col1, col2, col3, col4 = st.columns(4)
    stats = st.session_state.visualizer.get_statistics(filtered_df)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("📊 Tables", stats['total_tables'], help="Total number of data tables")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("🔗 Connections", stats['total_connections'], help="Total data flow connections")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("🔧 ETL Jobs", stats['total_jobs'], help="Total number of processing jobs")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("📋 Columns", stats['total_columns'], help="Unique columns being processed")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Create and display the visualization
    st.markdown("### 🏗️ Data Architecture Structure")
    
    with st.spinner('🔨 Building data architecture diagram...'):
        fig = st.session_state.visualizer.create_interactive_plot(filtered_df)
        st.plotly_chart(fig, use_container_width=True)
    
    # Legend explanation
    with st.expander("🎨 Color Legend & Guide"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **🎨 Table Colors:**
            - 🔴 **Red**: Source Systems (core_banking_system)
            - 🔵 **Blue**: Raw Data Tables (*_raw)
            - 🟢 **Green**: Dimension Tables (*_dim)
            - 🟠 **Orange**: Fact Tables (*_fact)
            - 🟣 **Purple**: Reporting Views (*_view)
            - 🔷 **Teal**: Access Layer (User access)
            """)
        with col2:
            st.markdown("""
            **🔗 Connection Lines:**
            - Each color represents a different ETL job
            - Arrows show data flow direction
            - Job labels show the process name
            - Hover for detailed information
            """)
    
    # Display filtered data table
    st.markdown("### 📋 Data Lineage Details")
    
    # Enhanced data display
    display_df = filtered_df.copy()
    display_df.index = range(1, len(display_df) + 1)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "source": st.column_config.TextColumn("📤 Source Table", width="medium"),
            "target": st.column_config.TextColumn("📥 Target Table", width="medium"),
            "column": st.column_config.TextColumn("📋 Column", width="small"),
            "job": st.column_config.TextColumn("🔧 ETL Job", width="small")
        }
    )
    
    # Export options
    st.markdown("### 💾 Export & Download")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Download Architecture Diagram", use_container_width=True):
            html_str = fig.to_html(include_plotlyjs='cdn')
            st.download_button(
                label="💾 Save as HTML",
                data=html_str,
                file_name=f"data_architecture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html"
            )
    
    with col2:
        if st.button("📋 Download Lineage Data", use_container_width=True):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="💾 Save as CSV",
                data=csv,
                file_name=f"lineage_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("📈 Generate Summary Report", use_container_width=True):
            report = f"""
# Data Architecture Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
- Total Tables: {stats['total_tables']}
- Total Connections: {stats['total_connections']}
- ETL Jobs: {stats['total_jobs']}
- Unique Columns: {stats['total_columns']}

## Data Flow Structure
{filtered_df.to_string(index=False)}
            """
            st.download_button(
                label="💾 Save Report",
                data=report,
                file_name=f"architecture_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    main()