import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
from pathlib import Path
import logging
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Data Loading and Preprocessing ---
def load_data(csv_path: Path) -> pd.DataFrame:
    """Loads and preprocesses data from a CSV file."""
    logging.info(f"Loading data from {csv_path}")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        logging.error(f"Data file not found at {csv_path}")
        raise
    
    df['pricingdate'] = pd.to_datetime(df['pricingdate'], errors='coerce') # Coerce errors for robustness
    df.dropna(subset=['pricingdate'], inplace=True) # Remove rows where date conversion failed

    # Handle 'Outlier': fillna with 0 and convert to int.
    df['Outlier'] = df['Outlier'].fillna(0).astype(int)
    # Handle 'Is Auction Date': fillna with 0 and convert to int.
    df['Is Auction Date'] = df['Is Auction Date'].fillna(0).astype(int)
    
    logging.info(f"Data loaded successfully. Shape: {df.shape}")
    return df

# --- Plot 1: Aggregated Time Series ---
def plot_aggregated_time_series(df: pd.DataFrame) -> go.Figure:
    """Creates an aggregated time series plot for 'bond' and 'future' products."""
    logging.info("Generating aggregated time series plot.")
    fig = go.Figure()
    products_to_plot = ['bond', 'future']
    # Filter for relevant products and make a copy to avoid SettingWithCopyWarning
    df_filtered = df[df['Product'].isin(products_to_plot)].copy()
    
    if df_filtered.empty:
        logging.warning("No data available for 'bond' or 'future' products in aggregated plot.")
        fig.update_layout(title_text="Aggregated Plot: No 'bond' or 'future' data available.")
        return fig

    df_filtered.sort_values('pricingdate', inplace=True)
    colors = {'bond': 'blue', 'future': 'green'}

    for product in products_to_plot:
        product_df = df_filtered[df_filtered['Product'] == product]
        if not product_df.empty:
            fig.add_trace(go.Scatter(
                x=product_df['pricingdate'],
                y=product_df['Validated Value Projected CV'],
                mode='lines+markers',
                name=f'{product.capitalize()} Value',
                line=dict(color=colors[product]),
                marker=dict(size=5)
            ))

            outliers_df = product_df[product_df['Outlier'] == 1]
            if not outliers_df.empty:
                fig.add_trace(go.Scatter(
                    x=outliers_df['pricingdate'],
                    y=outliers_df['Validated Value Projected CV'],
                    mode='markers',
                    name=f'{product.capitalize()} Outlier',
                    marker=dict(color='red', size=10, symbol='x'),
                    showlegend=True
                ))

    auction_dates_df = df_filtered[df_filtered['Is Auction Date'] == 1]
    unique_auction_dates = auction_dates_df['pricingdate'].unique()

    if len(unique_auction_dates) > 0:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='lines',
            name='Auction Date',
            line=dict(color='dimgray', dash='dash', width=1.5), # Changed color for better visibility
            showlegend=True
        ))
        for auction_date in unique_auction_dates:
            fig.add_vline(
                x=auction_date, line_width=1.5, line_dash="dash", line_color="dimgray" # Changed color
            )

    fig.update_layout(
        title_text="Aggregated Time Series: Validated Value Projected CV (Bond & Future)",
        xaxis_title="Pricing Date",
        yaxis_title="Validated Value Projected CV",
        legend_title_text="Legend", # Use legend_title_text for consistency
        hovermode="x unified"
    )
    return fig

# --- Plot 2: All Pillars Time Series (Subplots) ---
def plot_all_pillars_time_series(df: pd.DataFrame) -> go.Figure:
    """Creates time series plots for each Projected Pillar as subplots."""
    logging.info("Generating all pillars time series plot (subplots).")
    
    products_to_plot = ['bond', 'future']
    df_products_filtered = df[df['Product'].isin(products_to_plot)].copy()

    if df_products_filtered.empty:
        logging.warning("No data available for 'bond' or 'future' products in pillar-specific plot.")
        fig = go.Figure()
        fig.update_layout(title_text="Pillar-Specific Plots: No 'bond' or 'future' data available.")
        return fig

    df_products_filtered.sort_values('pricingdate', inplace=True)
    pillars = sorted(df_products_filtered['Projected Pillar'].unique())
    colors = {'bond': 'blue', 'future': 'green'}

    if not pillars:
        logging.warning("No projected pillars found for pillar-specific plots.")
        fig = go.Figure()
        fig.update_layout(title_text="Pillar-Specific Plots: No projected pillars available.")
        return fig

    num_pillars = len(pillars)
    num_cols = 2  # Or adjust as needed, e.g., 3
    num_rows = (num_pillars + num_cols - 1) // num_cols # Ceiling division

    subplot_titles = [str(p) for p in pillars]
    fig = make_subplots(
        rows=num_rows,
        cols=num_cols,
        subplot_titles=subplot_titles,
        vertical_spacing=0.15, # Adjust spacing as needed
        horizontal_spacing=0.1
    )

    for idx, pillar in enumerate(pillars):
        row = (idx // num_cols) + 1
        col = (idx % num_cols) + 1
        
        pillar_df = df_products_filtered[df_products_filtered['Projected Pillar'] == pillar]

        if pillar_df.empty:
            logging.warning(f"No data for pillar '{pillar}'. Skipping subplot.")
            # Add a dummy trace or annotation if you want to indicate an empty subplot
            fig.add_annotation(text=f"No data for pillar: {pillar}", row=row, col=col, showarrow=False)
            continue

        # Add traces for each product in this pillar's subplot
        for product in products_to_plot:
            product_pillar_df = pillar_df[pillar_df['Product'] == product]
            if not product_pillar_df.empty:
                fig.add_trace(go.Scatter(
                    x=product_pillar_df['pricingdate'],
                    y=product_pillar_df['Validated Value Projected CV'],
                    mode='lines+markers',
                    name=f'{product.capitalize()} ({pillar})',
                    legendgroup=f'product_{product}', # Group legends by product
                    showlegend=(idx == 0), # Show legend only for the first set of traces
                    line=dict(color=colors[product]),
                    marker=dict(size=5)
                ), row=row, col=col)

                outliers_df = product_pillar_df[product_pillar_df['Outlier'] == 1]
                if not outliers_df.empty:
                    fig.add_trace(go.Scatter(
                        x=outliers_df['pricingdate'],
                        y=outliers_df['Validated Value Projected CV'],
                        mode='markers',
                        name=f'{product.capitalize()} Outlier ({pillar})',
                        legendgroup=f'outlier_{product}', # Group outlier legends
                        showlegend=(idx == 0), # Show legend only for the first set
                        marker=dict(color='red', size=8, symbol='x'),
                    ), row=row, col=col)
        
        # Add vertical lines for auction dates
        auction_dates_pillar_df = pillar_df[pillar_df['Is Auction Date'] == 1]['pricingdate'].unique()
        for auction_date in auction_dates_pillar_df:
            fig.add_shape(
                type="line",
                x0=auction_date, y0=0,
                x1=auction_date, y1=1,
                yref="paper", # Relative to subplot y-axis
                line=dict(color="dimgray", width=1, dash="dash"),
                row=row, col=col
            )
        
        # Add a placeholder trace for the auction date legend for the first subplot only
        if idx == 0 and len(auction_dates_pillar_df) > 0:
             fig.add_trace(go.Scatter(
                 x=[None], y=[None], mode='lines',
                 name='Auction Date',
                 legendgroup='auction_date',
                 showlegend=True,
                 line=dict(color='dimgray', dash='dash', width=1.5)
             ), row=1, col=1) # Add to first subplot, won't display data but shows in legend

        fig.update_xaxes(title_text="Date", row=row, col=col)
        fig.update_yaxes(title_text="CV Value", row=row, col=col, autorange=True)


    fig.update_layout(
        title_text=f"Time Series by Projected Pillar (Bond & Future)",
        height=max(400 * num_rows, 600), # Adjust height based on number of rows
        # width=1200, # Adjust width as needed
        legend_title_text="Legend",
        hovermode="x unified" # Or "closest" if preferred for subplots
    )
    return fig

# --- Main Report Generation Function ---
def generate_financial_report(df: pd.DataFrame, output_html_path: Path):
    """Generates the full HTML report with both plots."""
    logging.info(f"Generating financial report to {output_html_path}")
    fig_agg = plot_aggregated_time_series(df.copy()) 
    fig_pillar = plot_all_pillars_time_series(df.copy())

    output_html_path.parent.mkdir(parents=True, exist_ok=True) 

    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE html><html><head><meta charset='utf-8' />")
        f.write("<title>Financial Products Visualization</title>")
        f.write("<style>body { font-family: Arial, sans-serif; margin: 20px; } h1 { color: #333; } hr { margin-top: 40px; margin-bottom: 40px; border: 1px solid #ddd; } </style>")
        f.write("</head><body>")
        
        f.write("<h1>Aggregated Time Series Plot</h1>")
        f.write(fig_agg.to_html(full_html=False, include_plotlyjs='cdn'))
        
        f.write("<hr>")
        f.write("<h1>Pillar-Specific Time Series Plot</h1>")
        f.write(fig_pillar.to_html(full_html=False, include_plotlyjs=False))
        
        f.write("</body></html>")
    logging.info(f"Report successfully generated: {output_html_path}")

# --- Main Execution ---
if __name__ == '__main__':
    project_root = Path(__file__).resolve().parent.parent
    input_dir = project_root / "Input"
    output_dir = project_root / "output"
    
    input_dir.mkdir(parents=True, exist_ok=True)

    data_file_name = 'Updated_IR_Delta.csv' 
    data_path = input_dir / data_file_name
    output_html_path = output_dir / 'financial_report.html'

    if not data_path.exists():
        logging.warning(f"Data file '{data_path}' not found. Creating dummy data.")
        
        num_points_per_set = 16 
        num_sets = 30 # Increased data for variety
        total_points = num_points_per_set * num_sets

        product_cycle = ['bond', 'future', 'bond', 'future', 'irdswap', 'bond', 'future', 'bond']
        pillar_values = ['100Y', '10Y', '15Y', '1M', '1W', '1Y', '20Y', '25Y', '2Y', '30Y', '3M', '40Y', '50Y', '5Y', '7Y', '6M'] # Ensure 16 unique pillars

        data = {
            'Product': [product_cycle[i % len(product_cycle)] for i in range(total_points)],
            'Projected Pillar': [pillar_values[i % len(pillar_values)] for i in range(total_points)],
            'pricingdate': pd.to_datetime(
                [f"{(i%12)+1}/{((i//12)%28)+1}/20{23+(i//(12*28))}" for i in range(total_points)] 
            ).strftime('%m/%d/%Y').tolist(),
            'Validated Value Projected CV': [100 + (i % 50) + (i // 50)*2 - (i%7)*3 for i in range(total_points)], 
            'Outlier': [1 if i % 13 == 0 else 0 for i in range(total_points)], # Varied outliers
            'Is Auction Date': [1 if i % 23 == 0 else 0 for i in range(total_points)] # Varied auction dates
        }
        
        df_dummy = pd.DataFrame(data)
        irdswap_indices = df_dummy[df_dummy['Product'] == 'irdswap'].index
        # Set some 'Outlier' to None for 'irdswap' product to simulate original data description
        df_dummy.loc[df_dummy.sample(frac=0.1, random_state=1).index.intersection(irdswap_indices), 'Outlier'] = None


        df_dummy.to_csv(data_path, index=False)
        logging.info(f"Dummy data saved to {data_path}")

    try:
        df_main = load_data(data_path)
        generate_financial_report(df_main, output_html_path)
        print(f"Financial report generated successfully: {output_html_path.resolve()}")
        print(f"To view the report, open this file in your browser: file:///{output_html_path.resolve().as_posix()}")
    except FileNotFoundError:
        print(f"ERROR: Input data file {data_path} was not found and dummy data creation might have failed or was skipped.")
    except Exception as e:
        logging.error(f"An error occurred during report generation: {e}", exc_info=True)
        print(f"An error occurred: {e}") 