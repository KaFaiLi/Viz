import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def _create_ftq_vs_rate_plot(output_html_file):
    """
    Creates the FTQ vs RATE plot with hardcoded data and saves it as an HTML file.
    """
    # Hardcoded data for FTQ vs RATE plot
    x_categories = ['1M', '3M', '5Y']
    ftq_values = {'FTQ1M': 100, 'FTQ3M': 150, 'FTQ5Y': 200}
    bar_y_values = [ftq_values['FTQ1M'], ftq_values['FTQ3M'], ftq_values['FTQ5Y']]
    bar_name = 'FTQ'
    bar_color = 'blue'
    bar_yaxis_title = 'FTQ Value'

    rate_values = {'RATE1M': 5.0, 'RATE3M': 5.5, 'RATE5Y': 6.0}
    line_y_values = [rate_values['RATE1M'], rate_values['RATE3M'], rate_values['RATE5Y']]
    line_name = 'RATE'
    line_color = 'red'
    line_yaxis_title = 'RATE (%)'
    
    main_title = 'Custom Plot: FTQ (Bar) vs. RATE (Line)'
    xaxis_title = 'Tenor'

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add bar trace
    fig.add_trace(
        go.Bar(x=x_categories, y=bar_y_values, name=bar_name, marker_color=bar_color),
        secondary_y=False,
    )

    # Add line trace
    fig.add_trace(
        go.Scatter(x=x_categories, y=line_y_values, name=line_name, mode='lines+markers', marker_color=line_color),
        secondary_y=True,
    )

    # Add figure title and x-axis title
    fig.update_layout(
        title_text=main_title,
        xaxis_title=xaxis_title
    )

    # Set y-axes titles
    fig.update_yaxes(title_text=f"<b>{bar_yaxis_title}</b>", secondary_y=False)
    fig.update_yaxes(title_text=f"<b>{line_yaxis_title}</b>", secondary_y=True)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_html_file), exist_ok=True)
    
    # Save plot to HTML file
    fig.write_html(output_html_file)
    print(f"Custom plot saved to {output_html_file}")
    return output_html_file

def _create_ftq_vs_irdelta_plot(output_html_file):
    """
    Creates the FTQ vs IRDelta plot with hardcoded data and saves it as an HTML file.
    """
    # Hardcoded data for FTQ vs IRDelta plot
    x_categories = ['1M', '3M', '5Y'] 
    ftq_values = {'FTQ1M': 100, 'FTQ3M': 150, 'FTQ5Y': 200} 
    bar_y_values = [ftq_values['FTQ1M'], ftq_values['FTQ3M'], ftq_values['FTQ5Y']]
    bar_name = 'FTQ'
    bar_color = 'green'
    bar_yaxis_title = 'FTQ Value'

    ir_delta_values = {'IRDelta1M': 0.5, 'IRDelta3M': 0.7, 'IRDelta5Y': 1.0} 
    line_y_values = [ir_delta_values['IRDelta1M'], ir_delta_values['IRDelta3M'], ir_delta_values['IRDelta5Y']]
    line_name = 'IRDelta'
    line_color = 'purple'
    line_yaxis_title = 'IRDelta Value'
    
    main_title = 'Custom Plot: FTQ (Bar) vs. IRDelta (Line)'
    xaxis_title = 'Tenor'
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add bar trace
    fig.add_trace(
        go.Bar(x=x_categories, y=bar_y_values, name=bar_name, marker_color=bar_color),
        secondary_y=False,
    )

    # Add line trace
    fig.add_trace(
        go.Scatter(x=x_categories, y=line_y_values, name=line_name, mode='lines+markers', marker_color=line_color),
        secondary_y=True,
    )

    # Add figure title and x-axis title
    fig.update_layout(
        title_text=main_title,
        xaxis_title=xaxis_title
    )

    # Set y-axes titles
    fig.update_yaxes(title_text=f"<b>{bar_yaxis_title}</b>", secondary_y=False)
    fig.update_yaxes(title_text=f"<b>{line_yaxis_title}</b>", secondary_y=True)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_html_file), exist_ok=True)
    
    # Save plot to HTML file
    fig.write_html(output_html_file)
    print(f"Custom plot saved to {output_html_file}")
    return output_html_file

def update_main_html(main_html_file, plot_configurations_list):
    """Update the main HTML dashboard to include multiple custom visualizations under a single section."""
    try:
        with open(main_html_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Main HTML file '{main_html_file}' not found. A template will be created.")
        # Create a dummy HTML file if it doesn't exist.
        content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        header { background-color: #333; color: #fff; padding: 10px 0; text-align: center; }
        .container { max-width: 1200px; margin: auto; overflow: hidden; padding: 0 20px; }
        .node-section { background-color: #fff; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .node-section h2 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }
        .metric-card { background-color: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; position: relative; }
        .metric-card .metric-type { display: block; font-size: 0.9em; color: #666; }
        .metric-card .metric-name { display: block; font-size: 1.1em; font-weight: bold; margin: 5px 0; }
        .metric-card a { position: absolute; top: 0; left: 0; width: 100%; height: 100%; text-decoration: none; }
        .metric-card a:hover { background-color: rgba(0,0,0,0.03); }
    </style>
</head>
<body>
    <header><h1>My Dashboard</h1></header>
    <div class="container">
        <!-- Existing content might be here -->
    </div>
</body>
</html>"""
        # Ensure the directory for main_html_file exists if we are creating it
        os.makedirs(os.path.dirname(main_html_file), exist_ok=True)

    all_metric_cards_html = ""
    for plot_config in plot_configurations_list:
        relative_plot_path = os.path.relpath(plot_config["plot_html_file"], os.path.dirname(main_html_file))
        
        metric_card_html = f'''
            <div class="metric-card">
                <span class="metric-type time-series">{plot_config["metric_type"]}</span>
                <span class="metric-name">{plot_config["metric_name"]}</span>
                <a href="{relative_plot_path}" target="_blank" aria-label="View {plot_config["metric_name"]}"></a>
            </div>'''
        all_metric_cards_html += metric_card_html
    
    # Create a single section for all custom plots
    new_section_html = f'''
    <section class="node-section">
        <h2>Custom Plots</h2>
        <div class="metrics-grid">
            {all_metric_cards_html}
        </div>
    </section>
    '''
    
    # Insert the new section before the closing body tag
    if '</body>' in content:
        content = content.replace('</body>', f'{new_section_html}</body>', 1)
    else:
        # If no body tag, append (basic fallback)
        content += new_section_html

    with open(main_html_file, 'w') as f:
        f.write(content)
    print(f"Main HTML file '{main_html_file}' updated to include the custom plots.")

def run_all_custom_visualizations():
    """Generates all custom plots and updates the main dashboard HTML."""
    # Get script's directory
    # This assumes the script is in src/ and paths are relative to the project root.
    # If custom_plot_visualization.py is run directly, __file__ gives its path.
    # If imported, and this function is called, we need to be careful about relative paths
    # if main.py is in a different location. For now, let's assume main.py is at project root.
    
    # Robustly determine workspace_root, assuming this file is in .../src/
    script_path_abspath = os.path.abspath(__file__)
    src_dir = os.path.dirname(script_path_abspath)
    workspace_root = os.path.dirname(src_dir) # Assumes src is directly under workspace root

    output_dir = os.path.join(workspace_root, "output")
    custom_plot_subdir_name = "Custom plot"
    custom_plots_output_dir = os.path.join(output_dir, custom_plot_subdir_name)

    # Ensure the custom plot output directory exists
    os.makedirs(custom_plots_output_dir, exist_ok=True)
    
    main_dashboard_html_file = os.path.join(output_dir, "index.html")

    # --- Plot 1: FTQ vs RATE ---
    ftq_rate_plot_html_file = os.path.join(custom_plots_output_dir, "ftq_vs_rate_plot.html")
    
    generated_ftq_rate_plot_path = _create_ftq_vs_rate_plot(
        output_html_file=ftq_rate_plot_html_file
    )

    # --- Plot 2: FTQ vs IRDelta ---
    ftq_irdelta_plot_html_file = os.path.join(custom_plots_output_dir, "ftq_vs_irdelta_plot.html")

    generated_ftq_irdelta_plot_path = _create_ftq_vs_irdelta_plot(
        output_html_file=ftq_irdelta_plot_html_file
    )
    
    # --- Update Main HTML with both plots ---
    plot_configs = [
        {
            "plot_html_file": generated_ftq_rate_plot_path,
            "metric_type": "Bar & Line Plot",
            "metric_name": "FTQ vs. RATE"
        },
        {
            "plot_html_file": generated_ftq_irdelta_plot_path,
            "metric_type": "Bar & Line Plot",
            "metric_name": "FTQ vs. IRDelta"
        }
    ]
    
    update_main_html(main_html_file=main_dashboard_html_file, plot_configurations_list=plot_configs)

    print("\nCustom plot generation and dashboard update finished.")
    print(f"1. FTQ vs RATE plot generated at: {generated_ftq_rate_plot_path}")
    print(f"2. FTQ vs IRDelta plot generated at: {generated_ftq_irdelta_plot_path}")
    print(f"3. Dashboard updated at: {main_dashboard_html_file}")
    print("   Open the dashboard in your browser to see the changes.")

if __name__ == "__main__":
    run_all_custom_visualizations() 