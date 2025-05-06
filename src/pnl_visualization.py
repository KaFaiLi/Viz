import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def load_data(file_path):
    """Load and preprocess the PNL and income attribution data."""
    df = pd.read_csv(file_path)
    
    # Calculate cumulative sum for the final result
    df['FINAL RESULT[LAST_FALSH].Daily_Cumulative'] = df['FINAL RESULT[LAST_FALSH].Daily'].cumsum()
    
    # Calculate cumulative sums for all attribution columns
    for col in df.columns:
        if '_L' in col and '.DtD' in col:
            df[f'{col}_Cumulative'] = df[col].cumsum()
    
    return df

def identify_level_columns(df):
    """Identify columns by their level (Mother, L1, L2, etc.) and group them."""
    level_groups = {}
    mother_level_key = "Mother"

    for col in df.columns:
        if col.endswith('_Cumulative'):
            continue

        if '.DtD' in col:
            if '_L' in col:
                try:
                    # Existing logic for L1, L2, etc.
                    level = col.split('_L')[1].split('.')[0]
                    # Ensure level is a numeric string for consistent key type
                    if not level.isdigit(): 
                        continue # Skip if level part is not purely numeric after _L
                    if level not in level_groups:
                        level_groups[level] = []
                    level_groups[level].append(col)
                except IndexError:
                    # Malformed column name, skip
                    continue
            else:
                # This is a "mother level" column
                if mother_level_key not in level_groups:
                    level_groups[mother_level_key] = []
                level_groups[mother_level_key].append(col)

    # Sort the levels: "Mother" first, then numeric levels
    sorted_level_keys = []
    if mother_level_key in level_groups and level_groups[mother_level_key]:
        sorted_level_keys.append(mother_level_key)
    
    numeric_keys = sorted([k for k in level_groups if k != mother_level_key and k.isdigit()], key=int)
    sorted_level_keys.extend(numeric_keys)
    
    # Add any other non-numeric, non-mother keys at the end, though typically not expected
    other_keys = sorted([k for k in level_groups if k != mother_level_key and not k.isdigit()])
    sorted_level_keys.extend(other_keys)

    return {key: level_groups[key] for key in sorted_level_keys if key in level_groups and level_groups[key]}

def create_multi_level_visualization(df, level_groups, output_dir):
    """Create a combined visualization with all levels in subplots."""
    num_levels = len(level_groups)
    
    # Create figure without secondary y-axes for each subplot
    fig = make_subplots(
        rows=num_levels, 
        cols=1,
        subplot_titles=[f'Level {level} - Cumulative Attribution & Result' for level in level_groups.keys()],
        vertical_spacing=0.15,  # Increased spacing between subplots
        # Remove specs for secondary_y
    )
    
    # Color palette for bars
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    
    # Add traces for each level
    for idx, (level, columns) in enumerate(level_groups.items(), 1):
        # Add stacked bars for each column in the level
        for col_idx, col in enumerate(columns):
            name = f"{col.split('_L')[0].strip()}"
            cumulative_col = f'{col}_Cumulative'
            
            fig.add_trace(
                go.Bar(
                    name=name,
                    x=df['Context.AsOfDate'],
                    y=df[cumulative_col],  # Use cumulative values
                    marker_color=colors[col_idx % len(colors)],
                    showlegend=True,
                    legendgroup=f"group{idx}",
                    legendgrouptitle_text=f"Level {level}",
                ),
                row=idx,
                col=1,
                # secondary_y=False, # This is the default, explicitly stating is fine or can be omitted
            )
        
        # Add line for cumulative final result on the primary y-axis
        fig.add_trace(
            go.Scatter(
                name='Cumulative Final Result',
                x=df['Context.AsOfDate'],
                y=df['FINAL RESULT[LAST_FALSH].Daily_Cumulative'],  # Use cumulative values
                line=dict(color='black', width=2),
                mode='lines',
                showlegend=True,
                legendgroup=f"group{idx}",
            ),
            row=idx,
            col=1,
            # secondary_y=True, # Remove this to use the primary y-axis
        )
        
        # Update axes labels for each subplot - now only one y-axis
        fig.update_xaxes(title_text="Date", row=idx, col=1)
        fig.update_yaxes(title_text="Cumulative Value", row=idx, col=1) # Unified Y-axis title
        # fig.update_yaxes(title_text="Cumulative Final Result", secondary_y=True, row=idx, col=1) # Remove this line
    
    # Update layout
    height_per_subplot = 400
    fig.update_layout(
        title='Cumulative PNL Attribution - All Levels',
        height=height_per_subplot * num_levels + 150,  # Additional space for title
        template='plotly_white',
        showlegend=True,
        # Place legend on the right side with separate groups
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05,
            traceorder='grouped',
            groupclick="toggleitem"
        ),
        # Adjust margins to accommodate legend
        margin=dict(r=150, t=100, b=50, l=50),
        # Set global barmode to stack
        barmode='stack',
        bargap=0.15,  # Add some gap between bars
        bargroupgap=0.1  # Add some gap between bar groups
    )
    
    # Save the figure
    output_path = os.path.join(output_dir, 'pnl_attribution_all_levels_cumulative.html')
    fig.write_html(output_path)
    return output_path

def update_dashboard_html(html_file, visualization_file):
    """Update the dashboard HTML to include the visualization."""
    with open(html_file, 'r') as f:
        content = f.read()
    
    # Create new section for PNL Attribution
    relative_path = os.path.relpath(visualization_file, os.path.dirname(html_file))
    new_section = f'''
    <section class="node-section">
        <h2>PNL Attribution</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <span class="metric-type time-series">Multi-Level Plot</span>
                <span class="metric-name">Cumulative PNL Attribution - All Levels</span>
                <a href="{relative_path}" target="_blank" aria-label="View Cumulative PNL Attribution All Levels"></a>
            </div>
        </div>
    </section>
    '''
    
    # Insert the new section before the closing body tag
    content = content.replace('</body>', f'{new_section}</body>')
    
    with open(html_file, 'w') as f:
        f.write(content)

def create_pnl_visualization(input_file=None, output_dir=None):
    """Main function to create PNL visualization that can be called from other scripts."""
    if input_file is None:
        input_file = 'Input/fake_pnl_IA.csv'
    if output_dir is None:
        output_dir = 'output'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load and process data
    df = load_data(input_file)
    level_groups = identify_level_columns(df)
    
    # Create visualization
    vis_file = create_multi_level_visualization(df, level_groups, output_dir)
    
    # Update dashboard
    dashboard_file = os.path.join(output_dir, 'index.html')
    update_dashboard_html(dashboard_file, vis_file)
    
    return vis_file

if __name__ == "__main__":
    create_pnl_visualization() 