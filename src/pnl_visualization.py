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
                    level = col.split('_L')[1].split('.')[0]
                    if level.isdigit():
                        level = f"_L{level}" # e.g. L1
                        if level not in level_groups:
                            level_groups[level] = []
                        level_groups[level].append(col)
                except IndexError:
                    continue # or handle error appropriately
            else: # if mother_level_key not in level_groups: # This was mother_level_key before
                if mother_level_key not in level_groups:
                    level_groups[mother_level_key] = []
                level_groups[mother_level_key].append(col)

    # Sort the levels: "Mother" first, then numeric levels sorted in ascending order
    sorted_level_keys = [mother_level_key] if mother_level_key in level_groups else []
    numeric_keys = sorted([k for k in level_groups if k.isdigit()], key=int)
    sorted_level_keys.extend(numeric_keys)

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
                    showlegend=(idx == 1), # Show legend only for the first subplot
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

def update_dashboard_html(html_file, visualization_files):
    """
    Update the dashboard HTML to include links to all yearly visualizations.
    Each year gets its own card with a link to the corresponding HTML file.
    """
    if not os.path.exists(html_file):
        raise FileNotFoundError(f"Dashboard HTML file not found: {html_file}")

    with open(html_file, "r") as f:
        content = f.read()

    new_section = '''
        <section class="node-section">
            <h2>PML Attribution by Year</h2>
            <div class="metrics-grid">
    '''
    for year, viz_file in sorted(visualization_files.items()):
        relative_path = os.path.relpath(viz_file, os.path.dirname(html_file))
        new_section += f'''
                <div class="metric-card">
                    <span class="metric-type time-series">{year}</span>
                    <span class="metric-name">Cumulative PML Attribution - All Levels</span>
                    <a href="{relative_path}" target="_blank" aria-label="View Cumulative PML Attribution for Year {year}">View Visualization</a>
                </div>
        '''
    new_section += '''
            </div>
        </section>
    '''

    content = content.replace('</body>', f'{new_section}</body>')

    with open(html_file, "w") as f:
        f.write(content)

def create_pnl_visualization(input_file=None, output_dir=None):
    """Main function to create PML visualizations by year and update dashboard HTML."""
    if input_file is None:
        input_file = 'input/fake_pnl_IA.csv' # Default input file
    if output_dir is None:
        output_dir = 'output' # Default output directory

    # Ensure the main output folder exists
    os.makedirs(output_dir, exist_ok=True)

    # Create a subfolder "Pnl Attribution" within the output folder to save all visualization files
    pnl_attr_dir = os.path.join(output_dir, "Pnl Attribution")
    os.makedirs(pnl_attr_dir, exist_ok=True)

    # Load and process data
    df = load_data(input_file)

    # Create visualizations for each year in the Pnl Attribution subfolder
    visualization_files = create_yearly_visualizations(df, pnl_attr_dir)

    # Update dashboard (index.html) with links to all yearly visualizations.
    # Assumes that the index.html file is located in the main output folder.
    dashboard_file = os.path.join(output_dir, 'index.html')
    update_dashboard_html(dashboard_file, visualization_files)

    return visualization_files

if __name__ == "__main__":
    create_pnl_visualization()