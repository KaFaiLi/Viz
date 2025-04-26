"""Module for generating HTML dashboard content."""

import logging
from pathlib import Path
from typing import Dict, List

class DashboardTemplate:
    """Class containing HTML templates and styling for the dashboard."""
    
    @staticmethod
    def get_css_variables():
        """Return the CSS variables used in the dashboard."""
        return """
            --primary-color: #2c3e50;
            --secondary-color: #34495e;
            --accent-color: #3498db;
            --text-color: #2c3e50;
            --background-color: #f5f6fa;
            --card-background: #ffffff;
            --hover-color: #e8f4f8;
            --timeseries-color: #3498db;
            --barplot-color: #2ecc71;
        """
    
    @staticmethod
    def get_css_styles():
        """Return the CSS styles for the dashboard."""
        return f"""
        :root {{
            {DashboardTemplate.get_css_variables()}
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            padding: 20px;
        }}
        
        .dashboard-header {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .dashboard-header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            text-align: center;
        }}
        
        .dashboard-header p {{
            text-align: center;
            opacity: 0.9;
        }}
        
        .node-section {{
            background: var(--card-background);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s ease;
        }}
        
        .node-section:hover {{
            transform: translateY(-2px);
        }}
        
        .node-section h2 {{
            color: var(--primary-color);
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
            border-bottom: 2px solid var(--accent-color);
            font-size: 1.8rem;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
        }}
        
        .metric-card {{
            position: relative;
            background: var(--card-background);
            border-radius: 8px;
            padding: 1.2rem;
            border: 1px solid #e1e1e1;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .metric-card:hover {{
            background: var(--hover-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}

        .metric-card a {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            text-decoration: none;
            opacity: 0;
            z-index: 1;
        }}
        
        .metric-type {{
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.85rem;
            margin-bottom: 0.8rem;
            color: white;
            position: relative;
            z-index: 0;
        }}

        .metric-type.time-series {{
            background: var(--timeseries-color);
        }}

        .metric-type.bar-plot {{
            background: var(--barplot-color);
        }}
        
        .metric-name {{
            display: block;
            color: var(--text-color);
            font-weight: 500;
            margin-top: 0.5rem;
            position: relative;
            z-index: 0;
        }}
        
        @media (max-width: 768px) {{
            .dashboard-header {{
                padding: 1.5rem;
            }}
            
            .dashboard-header h1 {{
                font-size: 2rem;
            }}
            
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
            
            .node-section {{
                padding: 1rem;
            }}
        }}
        """

class HTMLGenerator:
    """Class responsible for generating the HTML dashboard."""
    
    @staticmethod
    def generate_index_html(plot_infos: List[Dict], output_dir: Path) -> None:
        """
        Generate an index.html file linking to all plots.
        
        Args:
            plot_infos: List of dictionaries containing plot information
            output_dir: Directory where the index.html should be saved
        """
        index_path = output_dir / "index.html"
        logging.info(f"Generating index file at: {index_path}")

        # Group plots by stranaNode
        plots_by_node = HTMLGenerator._group_plots_by_node(plot_infos)
        
        # Generate HTML content
        html_content = HTMLGenerator._generate_html_content(plots_by_node, output_dir)

        # Write the file
        try:
            with open(index_path, 'w') as f:
                f.write(html_content)
            logging.info(f"Successfully generated index file: {index_path}")
        except IOError as e:
            logging.error(f"Error writing index file {index_path}: {e}")

    @staticmethod
    def _group_plots_by_node(plot_infos: List[Dict]) -> Dict[str, List[Dict]]:
        """Group plot information by stranaNode."""
        plots_by_node = {}
        for info in plot_infos:
            node = info['strana_node']
            if node not in plots_by_node:
                plots_by_node[node] = []
            plots_by_node[node].append(info)
        return plots_by_node

    @staticmethod
    def _generate_html_content(plots_by_node: Dict[str, List[Dict]], output_dir: Path) -> str:
        """Generate the complete HTML content for the dashboard."""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Risk Metrics Dashboard</title>
    <style>
        {DashboardTemplate.get_css_styles()}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1>Risk Metrics Dashboard</h1>
        <p> Visualization of financial risk metrics and time series data</p>
    </div>
"""

        # Sort nodes alphabetically
        sorted_nodes = sorted(plots_by_node.keys())

        for node in sorted_nodes:
            html_content += HTMLGenerator._generate_node_section(node, plots_by_node[node], output_dir)

        html_content += """
</body>
</html>
"""
        return html_content

    @staticmethod
    def _generate_node_section(node: str, plots: List[Dict], output_dir: Path) -> str:
        """Generate HTML content for a single node section."""
        section_content = f"""
    <section class="node-section">
        <h2>{node}</h2>
        <div class="metrics-grid">
"""
        # Sort plots within each node for consistency
        sorted_plots = sorted(plots, key=lambda x: (x['plot_type'], 
                            ",".join(x['metrics']) if isinstance(x['metrics'], list) else x['metrics']))
        
        for info in sorted_plots:
            plot_type_display = "Bar Plot" if info['plot_type'] == 'bar' else "Time Series"
            plot_type_class = "bar-plot" if info['plot_type'] == 'bar' else "time-series"
            metrics_display = ", ".join(info['metrics']) if isinstance(info['metrics'], list) else info['metrics']
            relative_path = Path(info['output_file']).relative_to(output_dir)
            
            section_content += f"""
            <div class="metric-card">
                <span class="metric-type {plot_type_class}">{plot_type_display}</span>
                <span class="metric-name">{metrics_display}</span>
                <a href="{relative_path}" target="_blank" aria-label="View {metrics_display} {plot_type_display}"></a>
            </div>"""
        
        section_content += """
        </div>
    </section>"""
        
        return section_content 