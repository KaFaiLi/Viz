import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import numpy as np

def load_data(file_path):
    """Load and preprocess the PML and income attribution data."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    df = pd.read_csv(file_path)

    # Remove columns with all null values
    df = df.dropna(axis=1, how='all')

    # Fill null values with 0
    df = df.fillna(0)

    # Convert Context.AsOfDate to datetime and extract year
    if 'Context.AsOfDate' in df.columns:
        df['Context.AsOfDate'] = pd.to_datetime(df['Context.AsOfDate'])
        df['Year'] = df['Context.AsOfDate'].dt.year
    else:
        raise KeyError("The required column 'Context.AsOfDate' is missing in the input data.")

    # Check if the required column exists
    if 'PnL Explanation.DTD' not in df.columns:
        raise KeyError("The required column 'PnL Explanation.DTD' is missing in the input data.")

    # Calculate cumulative sum for the PnL Explanation.DTD for each year
    df['PnL Explanation.DTD_Cumulative'] = df.groupby('Year')['PnL Explanation.DTD'].cumsum()

    # Calculate cumulative sums for all attribution columns (within each year)
    for col in df.columns:
        # skip non-attribution columns
        if col.endswith('_Cumulative') or col == "PnL Explanation.DTD" or col in ["Context.AsOfDate", "Year"]:
            continue

        if 'L' in col and '.DTD' in col:
            df[f'{col}_Cumulative'] = df.groupby('Year')[col].cumsum()
        elif '.DTD' in col and 'L' not in col: # Handle "Mother" level columns
            df[f'{col}_Cumulative'] = df.groupby('Year')[col].cumsum()
    return df

def identify_level_columns(df):
    """Identifies columns by their level (Mother, L1, L2, etc.) and group them."""
    level_groups = {}
    mother_level_key = "Mother"

    for col in df.columns:
        # Skip cumulative columns and the primary PnL Explanation column
        if col.endswith('_Cumulative'):
            continue
        if col == 'PnL Explanation.DTD':
            continue

        if '.DTD' in col:
            if '_L' in col:
                try:
                    # Parse the level (e.g., L1, L2, etc.)
                    level_part = col.split('_L')[1].split('.')[0] # Changed variable name from level to level_part
                    if level_part.isdigit(): # Check if level_part is a digit
                        level = f"_L{level_part}" # e.g. _L1
                        if level not in level_groups:
                            level_groups[level] = []
                        level_groups[level].append(col)
                except IndexError:
                    continue # or handle error appropriately
            else: 
                if mother_level_key not in level_groups:
                    level_groups[mother_level_key] = []
                level_groups[mother_level_key].append(col)

    # Sort the levels: "Mother" first, then numeric levels (_L1, _L2) sorted correctly
    sorted_level_keys = []
    if mother_level_key in level_groups:
        sorted_level_keys.append(mother_level_key)
    
    # Extract and sort numeric keys like _L1, _L2
    numeric_keys = sorted(
        [k for k in level_groups if k.startswith('_L') and k[2:].isdigit()],
        key=lambda k: int(k[2:])
    )
    sorted_level_keys.extend(numeric_keys)
    
    # Add any other keys that might not fit the pattern (e.g., if new levels are added without "_L" prefix)
    # This part might need adjustment if other patterns exist.
    other_keys = sorted([k for k in level_groups if k not in sorted_level_keys])
    sorted_level_keys.extend(other_keys)


    return {key: level_groups[key] for key in sorted_level_keys if key in level_groups}


def create_yearly_visualizations(df, viz_output_dir):
    """
    Create separate visualizations for each year and save them as HTML files.
    Each visualization shows multi-level cumulative attribution and the PnL Explanation line.
    The x-axis uses a categorical format (with a subset of tick labels) to avoid white spaces.
    """
    visualization_files = {}
    years = sorted(df['Year'].unique())

    for year in years:
        df_year = df[df['Year'] == year].copy().sort_values("Context.AsOfDate")

        # Create a new column with formatted date strings (e.g., 'Dec 12, 2024')
        df_year['formattedDate'] = df_year['Context.AsOfDate'].dt.strftime('%b %d, %Y')

        # Compute a subset of tick values for the x-axis to avoid clutter
        unique_dates = list(dict.fromkeys(df_year['formattedDate']).keys()) # Preserve order
        if len(unique_dates) > 10:
            indices = np.linspace(0, len(unique_dates) - 1, 10, dtype=int)
            tickvals = [unique_dates[i] for i in indices]
        else:
            tickvals = unique_dates

        level_groups = identify_level_columns(df_year)
        num_levels = len(level_groups)
        if num_levels == 0: # No attribution columns found for this year
            continue

        # Create figure with a subplot per attribution level
        fig = make_subplots(
            rows=num_levels,
            cols=1,
            subplot_titles=[f'{level} (Year {year}) Cumulative Attribution & Result' for level in level_groups.keys()],
            vertical_spacing=0.15,
        )

        colors = ['#f1b7b4', '#ffd7d4', '#e2a92c', '#ddb27d', '#9a67bd',
                  '#b086d0', '#c7a7e2', '#877f7f', '#acb0d2', '#75aecf']


        for idx, (level, columns) in enumerate(level_groups.items()):
            row_idx = idx + 1
            for col_idx, col in enumerate(columns):
                base_name = col.split('.')[0].strip() # If 'L' in col else col.split('.')[0].strip()
                name = f"Level {level}: {base_name}"
                cumulative_col = f'{col}_Cumulative'
                fig.add_trace(
                    go.Bar(
                        name=name,
                        x=df_year['formattedDate'],
                        y=df_year[cumulative_col],
                        marker_color=colors[col_idx % len(colors)],
                        showlegend=True,
                    ),
                    row=row_idx,
                    col=1,
                )

            fig.add_trace(
                go.Scatter(
                    name='Cumulative PnL Explanation',
                    x=df_year['formattedDate'],
                    y=df_year['PnL Explanation.DTD_Cumulative'],
                    line=dict(color='black', width=2),
                    mode='lines',
                    showlegend=(idx == 0), # Show legend only for the first subplot for consistency
                ),
                row=row_idx,
                col=1,
            )

            # Update x-axis for each subplot:
            # Use a categorical type (to remove gaps) and specify a subset of tick values
            fig.update_xaxes(
                title_text="Date",
                row=row_idx,
                col=1,
                type="category",
                tickmode="array",
                tickvals=tickvals,
            )
            fig.update_yaxes(title_text="Cumulative Value", row=idx+1, col=1) # Corrected loop variable

        fig.update_layout(
            title_text=f'Cumulative PML Attribution - All Levels for {year}',
            height=400 * num_levels + 150,
            # width=1200, # Adjust as needed
            plot_bgcolor='plotly_white',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99, # Adjusted y to be just below the title
                xanchor="left",
                x=1.05, # Adjusted x to be to the right of the plots
                traceorder='normal',
            ),
            barmode='relative', # Stack bars
            bargap=0.15,
            bargroupgap=0.1
        )

        output_path = os.path.join(viz_output_dir, f'pnl_attribution_all_levels_cumulative_{year}.html')
        fig.write_html(output_path)
        visualization_files[year] = output_path

    return visualization_files

def create_all_years_visualization(df, viz_output_dir):
    """
    Create a single visualization for all years combined.
    Cumulative sums are calculated per year and then plotted continuously.
    The x-axis uses a categorical format.
    """
    df_all_years = df.copy().sort_values("Context.AsOfDate")

    df_all_years['formattedDate'] = df_all_years['Context.AsOfDate'].dt.strftime('%b %d, %Y')

    unique_dates = list(dict.fromkeys(df_all_years['formattedDate']).keys())
    if len(unique_dates) > 20: 
        indices = np.linspace(0, len(unique_dates) - 1, 20, dtype=int)
        tickvals = [unique_dates[i] for i in indices]
    else:
        tickvals = unique_dates

    level_groups = identify_level_columns(df_all_years)
    num_levels = len(level_groups)
    if num_levels == 0:
        print("No attribution columns found for the 'All Years' visualization.")
        return None

    fig = make_subplots(
        rows=num_levels,
        cols=1,
        subplot_titles=[f'{level} (All Years) Cumulative Attribution & Result' for level in level_groups.keys()],
        vertical_spacing=0.15,
    )

    colors = ['#f1b7b4', '#ffd7d4', '#e2a92c', '#ddb27d', '#9a67bd',
              '#b086d0', '#c7a7e2', '#877f7f', '#acb0d2', '#75aecf']

    for idx, (level, columns) in enumerate(level_groups.items()):
        row_idx = idx + 1
        for col_idx, col in enumerate(columns):
            base_name = col.split('.')[0].strip()
            name = f"Level {level}: {base_name}"
            cumulative_col = f'{col}_Cumulative'
            fig.add_trace(
                go.Bar(
                    name=name,
                    x=df_all_years['formattedDate'],
                    y=df_all_years[cumulative_col],
                    marker_color=colors[col_idx % len(colors)],
                    showlegend=True,
                ),
                row=row_idx,
                col=1,
            )

        fig.add_trace(
            go.Scatter(
                name='Cumulative PnL Explanation',
                x=df_all_years['formattedDate'],
                y=df_all_years['PnL Explanation.DTD_Cumulative'],
                line=dict(color='black', width=2),
                mode='lines',
                showlegend=(idx == 0), 
            ),
            row=row_idx,
            col=1,
        )

        fig.update_xaxes(
            title_text="Date",
            row=row_idx,
            col=1,
            type="category",
            tickmode="array",
            tickvals=tickvals,
        )
        fig.update_yaxes(title_text="Cumulative Value", row=row_idx, col=1)

    fig.update_layout(
        title_text='Cumulative PML Attribution - All Levels (All Years)',
        height=400 * num_levels + 150,
        plot_bgcolor='plotly_white',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05,
            traceorder='normal',
        ),
        barmode='relative',
        bargap=0.15,
        bargroupgap=0.1
    )

    output_filename = 'pnl_attribution_all_levels_cumulative_all_years.html'
    output_path = os.path.join(viz_output_dir, output_filename)
    fig.write_html(output_path)
    
    return {"All Years": output_path}

def update_dashboard_html(html_file, visualization_files):
    """
    Update the dashboard HTML to include links to all yearly visualizations
    and the combined "All Years" visualization.
    Each entry gets its own card with a link to the corresponding HTML file.
    Uses HTML comments to make updates idempotent.
    """
    if not os.path.exists(html_file):
        print(f"Dashboard HTML file not found: {html_file}. Creating a basic one.")
        basic_html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PML Visualization Dashboard</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        h1, h2 { color: #333; }
        .node-section { background-color: #fff; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
        .metric-card { background-color: #e9ecef; padding: 15px; border-radius: 4px; text-align: center; }
        .metric-card .metric-type { display: block; font-size: 1.2em; font-weight: bold; margin-bottom: 5px; color: #007bff; }
        .metric-card .metric-name { display: block; font-size: 0.9em; margin-bottom: 10px; color: #555; height: 40px; } /* Added height for consistency */
        .metric-card a { display: inline-block; padding: 8px 15px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; transition: background-color 0.3s ease; }
        .metric-card a:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <h1>PML Visualization Dashboard</h1>
    <!-- PML_ATTRIBUTION_SECTION_START -->
    <!-- Existing content will be replaced or this section will be filled -->
    <!-- PML_ATTRIBUTION_SECTION_END -->
</body>
</html>
"""
        with open(html_file, "w") as f:
            f.write(basic_html_content)

    with open(html_file, "r") as f:
        content = f.read()

    section_start_marker = "<!-- PML_ATTRIBUTION_SECTION_START -->"
    section_end_marker = "<!-- PML_ATTRIBUTION_SECTION_END -->"

    new_section_inner_content = f'''
        <section class="node-section">
            <h2>PML Attribution Analysis</h2>
            <div class="metrics-grid">
    '''
    
    # Sort keys: "All Years" first, then numeric years ascending.
    sorted_keys = sorted(visualization_files.keys(), key=lambda k: (str(k) != "All Years", k))

    for key in sorted_keys:
        viz_file = visualization_files[key]
        # Ensure relative_path uses forward slashes for HTML compatibility
        relative_path = os.path.relpath(viz_file, os.path.dirname(html_file)).replace("\\", "/")
        
        display_name = str(key)
        card_title = "Cumulative PML Attribution - All Levels"
        aria_label_detail = f"for {key}"

        if key == "All Years":
            card_title = "Cumulative PML Attribution - All Levels (All Years)"
            aria_label_detail = "(All Years)"
        
        new_section_inner_content += f'''
                <div class="metric-card">
                    <span class="metric-type time-series">{display_name}</span>
                    <span class="metric-name">{card_title}</span>
                    <a href="{relative_path}" target="_blank" aria-label="View {card_title} {aria_label_detail}">View Visualization</a>
                </div>
        '''
    new_section_inner_content += '''
            </div>
        </section>
    '''

    # Construct the full new section with markers
    full_new_section = f"{section_start_marker}\n{new_section_inner_content}\n{section_end_marker}"

    start_idx = content.find(section_start_marker)
    end_idx = content.find(section_end_marker)

    if start_idx != -1 and end_idx != -1:
        # Replace existing section
        content = content[:start_idx] + full_new_section + content[end_idx + len(section_end_marker):]
    else:
        # Append new section before </body> if markers are not found
        # This might happen if the initial HTML doesn't have the markers
        body_end_tag = '</body>'
        if body_end_tag in content:
            content = content.replace(body_end_tag, f'{full_new_section}\n{body_end_tag}')
        else: # Fallback if no </body> tag, append to end (less ideal)
            content += f'\n{full_new_section}'
        
    with open(html_file, "w") as f:
        f.write(content)

def create_pnl_visualization(input_file=None, output_dir=None):
    """Main function to create PML visualizations by year and update dashboard HTML."""
    if input_file is None:
        input_file = 'input/fake_pnl_IA.csv' 
    if output_dir is None:
        output_dir = 'output' 

    os.makedirs(output_dir, exist_ok=True)
    pnl_attr_dir = os.path.join(output_dir, "Pnl Attribution")
    os.makedirs(pnl_attr_dir, exist_ok=True)

    df = load_data(input_file)

    visualization_files = create_yearly_visualizations(df, pnl_attr_dir)

    all_years_viz_info = create_all_years_visualization(df, pnl_attr_dir)
    if all_years_viz_info:
        visualization_files.update(all_years_viz_info)

    dashboard_file = os.path.join(output_dir, 'index.html')
    if not os.path.exists(dashboard_file):
        # If index.html absolutely does not exist, create a minimal one with markers
        # The update_dashboard_html function will also handle this, but this is an earlier check.
        print(f"Dashboard HTML file {dashboard_file} not found. A basic one will be created by update_dashboard_html.")

    update_dashboard_html(dashboard_file, visualization_files)

    return visualization_files

if __name__ == "__main__":
    create_pnl_visualization()