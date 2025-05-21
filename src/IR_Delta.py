import pandas as pd
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def get_maturity_in_years(maturity_str):
    """
    Converts a maturity string to a numeric value in years.
    Assumptions:
        - If the string ends with 'Y', the number before 'Y' is in years.
        - If it ends with 'M', the number is in months (1 month = 1/12 years).
        - If it ends with 'W', the number is in weeks (1 week = 1/52 years).
    """
    if maturity_str.endswith('Y'):
        return float(maturity_str[:-1])
    elif maturity_str.endswith('M'):
        return float(maturity_str[:-1]) / 12.0
    elif maturity_str.endswith('W'):
        return float(maturity_str[:-1]) / 52.0
    else:
        raise ValueError(f"Unrecognized maturity unit in '{maturity_str}'")

def generate_time_series_plots(df, specific_pillar=None, fig_width=1800, plot_height=400):
    """
    Creates time series plots for each Projected Pillar with all available products.
    Subplots are sorted by maturity. Each subplot is wider, vertical grey lines mark auction
    dates, product colors are kept consistent, and outliers are marked with different colors
    based on the product type:
        - Bond Outliers: Yellow triangles.
        - Future Outliers: Green triangles.

    Colors mapped for the product main lines:
        - Bond: Blue
        - Future: Red
        - IrdSwap: Orange
        - repo: Pink

    The legend is grouped by the subplot (pillar). For each pillar, the first product trace
    includes a legend group title (the pillar name), and all product traces use the same legend
    group (the pillar name).

    Parameters:
        df (pandas.DataFrame): DataFrame containing the following columns:
            'Product': Categories (e.g., 'bond', 'future', 'irdswap', 'repo')
            'Projected Pillar': Maturity identifiers (e.g., '6M', '10Y', '15Y', '1M', etc.)
            'pricingdate': Date string in format '%m/%d/%Y' (e.g., '2/28/2023')
            'Validated Value Projected CV': Float values.
            'Outlier': Binary indicator (0/1), with potential nulls for 'irdswap'
            'Is Auction Date': Binary indicator (0/1)
        specific_pillar (str, optional): If provided, will generate the plot for this pillar only.
        fig_width (int, optional): The overall figure width.
        plot_height (int, optional): The base height for each subplot row; overall height is plot_height * number of rows.

    Returns:
        fig (plotly.graph_objects.Figure): Plotly Figure object with the time series visualizations.
    """
    # Define a consistent color mapping for each product.
    color_map = {
        'bond': 'blue',
        'future': 'red',
        'irdswap': 'orange',
        'repo': 'pink'
    }

    # Define outlier colors for specific products.
    outlier_color_map = {
        'bond': 'yellow',
        'future': 'green'
    }

    # Data cleaning.
    df['Projected Pillar'] = df['Projected Pillar'].astype(str).str.strip()
    df['Product'] = df['Product'].astype(str).str.strip()
    df['pricingdate'] = pd.to_datetime(df['pricingdate'], format='%m/%d/%Y', errors='coerce')

    if specific_pillar:
        specific_pillar = specific_pillar.strip()
        pillar_list = [specific_pillar]
        df = df[df['Projected Pillar'] == specific_pillar]
    else:
        pillar_list = list(df['Projected Pillar'].dropna().unique())
        # Sort pillars by maturity
        pillar_list = sorted(pillar_list, key=get_maturity_in_years)

    n_pillars = len(pillar_list)
    if n_pillars == 0:
        raise ValueError("No valid Projected Pillar found in the dataset for plotting.")

    # Arrange subplots: 2 per row.
    num_cols = 2
    num_rows = math.ceil(n_pillars / num_cols)
    fig = make_subplots(rows=num_rows, cols=num_cols, subplot_titles=pillar_list)

    # Iterate over each pillar (subplot).
    for i, pillar in enumerate(pillar_list):
        row = i // num_cols + 1
        col = i % num_cols + 1

        # Filter data for the current pillar and sort by date.
        pillar_df = df[df['Projected Pillar'] == pillar].sort_values(by='pricingdate')
        product_list = sorted(pillar_df['Product'].dropna().unique())

        # Flag to check if the legend group title for this pillar has been added.
        grouptitleadded = False

        for product in product_list:
            product_df = pillar_df[pillar_df['Product'] == product].sort_values(by='pricingdate')
            if product_df.empty:
                continue

            # Determine product color.
            product_key = product.lower()
            prod_color = color_map.get(product_key, 'black') # Default to black if not specified

            # Set legend grouping: use the pillar name as the legend group.
            if not grouptitleadded:
                # For the first product in this subplot, add the legend group title.
                legend_args = {
                    "legendgroup": pillar,
                    "legendgrouptitle": {"text": pillar},
                    "showlegend": True,
                    "name": product,
                }
                grouptitleadded = True
            else:
                legend_args = {
                    "legendgroup": pillar,
                    "name": product,
                    "showlegend": True
                }

            # Main trace for the product line.
            fig.add_trace(
                go.Scatter(
                    x=product_df['pricingdate'],
                    y=product_df['Validated Value Projected CV'],
                    mode='lines',
                    line=dict(width=2, color=prod_color),
                    **legend_args
                ),
                row=row, col=col
            )

            # Outlier markers with different colors for bond and future.
            product_outliers = product_df[product_df['Outlier'] == 1]
            if not product_outliers.empty:
                outlier_color = outlier_color_map.get(product_key, 'yellow') # Default to yellow if not specified.
                fig.add_trace(
                    go.Scatter(
                        x=product_outliers['pricingdate'],
                        y=product_outliers['Validated Value Projected CV'],
                        mode='markers',
                        marker=dict(color=outlier_color, size=7, symbol='triangle-up'),
                        name=f"{product} Outlier",
                        legendgroup=pillar,
                        showlegend=False
                    ),
                    row=row, col=col
                )

        # Auction dates: add vertical grey lines.
        # Note: This part uses product_df, which refers to the *last* product in the loop for auction dates.
        # If auction dates are common for the pillar, this is fine. If they are product-specific,
        # this might need adjustment or use pillar_df for auction dates if applicable.
        if not pillar_df.empty: # Use pillar_df to find auction dates for the whole pillar
            pillar_auction_dates = pillar_df[pillar_df['Is Auction Date'] == 1]['pricingdate'].unique()
            for auction_date in pillar_auction_dates:
                fig.add_vline(
                    x=auction_date,
                    line=dict(color='lightgrey', width=1),
                    row=row,
                    col=col
                )

        # Set axis titles for this subplot.
        fig.update_xaxes(title_text="pricingdate", row=row, col=col)
        fig.update_yaxes(title_text="Validated Value Projected CV", row=row, col=col)

    # Update overall layout.
    fig.update_layout(
        height=plot_height * num_rows,
        width=fig_width,
        title_text="Time Series Plots of Validated Value Projected CV by Projected Pillar",
        legend_title_text="Product",
        margin=dict(t=80) # Adjust top margin for main title
    )
    return fig

def generate_product_sum_plot(df, fig_width=1800, plot_height=600):
    """
    Creates a time series plot showing the sum of 'Validated Value Projected CV' for each product
    across all pillars, and an aggregated line for the sum of all products. Vertical grey lines
    mark auction dates.

    Parameters:
        df (pandas.DataFrame): DataFrame containing the following columns:
            'Product': Categories (e.g., 'bond', 'future', 'irdswap', 'repo')
            'pricingdate': Date string in format '%m/%d/%Y' (e.g., '2/28/2023')
            'Validated Value Projected CV': Float values.
            'Is Auction Date': Binary indicator (0/1)
        fig_width (int, optional): The overall figure width.
        plot_height (int, optional): The height for the plot.

    Returns:
        fig (plotly.graph_objects.Figure): Plotly Figure object with the time series visualizations.
    """
    # Define a consistent color mapping for each product.
    color_map = {
        'bond': 'blue',
        'future': 'red',
        'irdswap': 'orange',
        'repo': 'pink',
        'Total': 'black' # Color for the aggregated line
    }

    # Data cleaning and preparation
    df_plot = df.copy()
    df_plot['Product'] = df_plot['Product'].astype(str).str.strip()
    df_plot['pricingdate'] = pd.to_datetime(df_plot['pricingdate'], format='%m/%d/%Y', errors='coerce')

    # Group by pricingdate and Product, then sum 'Validated Value Projected CV'
    product_sum_df = df_plot.groupby(['pricingdate', 'Product'])['Validated Value Projected CV'].sum().unstack(fill_value=0)

    # Calculate the total sum across all products for each date
    product_sum_df['Total'] = product_sum_df.sum(axis=1)

    fig = go.Figure()

    # Add traces for each product
    for product in product_sum_df.columns:
        if product == 'Total': # Skip the total for now, add it last so it's on top or styled differently if needed
            continue
        prod_color = color_map.get(product.lower(), 'grey') # Default color if not in map
        fig.add_trace(go.Scatter(
            x=product_sum_df.index,
            y=product_sum_df[product],
            mode='lines',
            name=product,
            line=dict(color=prod_color, width=2)
        ))

    # Add trace for the aggregated sum
    fig.add_trace(go.Scatter(
        x=product_sum_df.index,
        y=product_sum_df['Total'],
        mode='lines',
        name='Total (All Products)',
        line=dict(color=color_map['Total'], width=3, dash='dash') # Thicker, dashed line for total
    ))

    # Add vertical lines for auction dates
    auction_dates = df_plot[df_plot['Is Auction Date'] == 1]['pricingdate'].unique()
    for auction_date in auction_dates:
        fig.add_vline(
            x=auction_date,
            line=dict(color='lightgrey', width=1)
        )

    # Update layout
    fig.update_layout(
        title_text="Sum of Validated Value Projected CV by Product and Total",
        xaxis_title="pricingdate",
        yaxis_title="Sum of Validated Value Projected CV",
        height=plot_height,
        width=fig_width,
        legend_title_text="Product Category",
        margin=dict(t=80)
    )

    return fig

def update_index_html(plot_info_list, index_path="output/index.html", output_plot_dir="Custom plot"):
    """
    Updates the index.html file to include new plot entries in the "Custom Plots" section.

    Parameters:
        plot_info_list (list of dict): Each dict should contain:
            'name': Display name of the plot.
            'filename': Filename of the plot (e.g., 'my_plot.html').
            'type_text': Text for the metric type span (e.g., 'Time Series').
            'type_class': CSS class for the metric type (e.g., 'time-series').
        index_path (str): Path to the index.html file.
        output_plot_dir (str): The directory name used in hrefs, relative to index.html.
    """
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: {index_path} not found.")
        return
    except Exception as e:
        print(f"Error reading {index_path}: {e}")
        return

    generated_html_for_insertion = ""
    for plot in plot_info_list:
        plot_html = (
            f"            <div class=\"metric-card\">\n"
            f"                <span class=\"metric-type {plot['type_class']}\">{plot['type_text']}</span>\n"
            f"                <span class=\"metric-name\">{plot['name']}</span>\n"
            f"                <a href=\"{output_plot_dir}/{plot['filename']}\" target=\"_blank\" aria-label=\"View {plot['name']}\"></a>\n"
            f"            </div>\n"
        )
        generated_html_for_insertion += plot_html
    
    if not generated_html_for_insertion:
        print("No plot information provided to update index.html.")
        return

    custom_plots_header_marker = "<h2>Custom Plots</h2>"
    header_idx = html_content.find(custom_plots_header_marker)
    if header_idx == -1:
        print(f"Error: Marker '{custom_plots_header_marker}' not found in {index_path}.")
        return

    metrics_grid_open_tag = '<div class="metrics-grid">'
    grid_open_idx = html_content.find(metrics_grid_open_tag, header_idx + len(custom_plots_header_marker))
    if grid_open_idx == -1:
        print(f"Error: '{metrics_grid_open_tag}' not found after '{custom_plots_header_marker}' in {index_path}.")
        return

    search_start_pos = grid_open_idx + len(metrics_grid_open_tag)
    search_boundary_for_divs = html_content.find("</section>", grid_open_idx)
    if search_boundary_for_divs == -1:
        print(f"Error: Could not find closing </section> for the Custom Plots section to limit div search.")
        return

    open_div_count = 1 
    current_pos = search_start_pos
    insertion_point = -1

    while current_pos < search_boundary_for_divs:
        next_potential_open_div = html_content.find("<div", current_pos, search_boundary_for_divs)
        next_close_div = html_content.find("</div>", current_pos, search_boundary_for_divs)

        if next_close_div == -1:
            print(f"Error: Malformed HTML. No '</div>' found before section end in Custom Plots.")
            return

        if next_potential_open_div != -1 and next_potential_open_div < next_close_div:
            open_div_count += 1
            current_pos = next_potential_open_div + len("<div")
        else:
            open_div_count -= 1
            if open_div_count == 0: 
                insertion_point = next_close_div
                break
            current_pos = next_close_div + len("</div>")
    
    if insertion_point == -1:
        print(f"Error: Could not find the closing '</div>' for metrics-grid in {index_path} within the Custom Plots section.")
        return

    updated_html_content = html_content[:insertion_point] + generated_html_for_insertion + html_content[insertion_point:]

    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(updated_html_content)
        print(f"Successfully updated {index_path} with new plot entries.")
    except Exception as e:
        print(f"Error writing updated {index_path}: {e}")

# Example usage:
if __name__ == "__main__":
    # Define the output directory for plots (relative to script execution location)
    plot_save_dir = "output/Custom_plot"
    os.makedirs(plot_save_dir, exist_ok=True)

    # Load data (ensure this path is correct relative to script execution location)
    try:
        df_sample = pd.read_csv("input/updated_IR_Delta.csv")
    except FileNotFoundError:
        print("Error: input/updated_IR_Delta.csv not found. Make sure the path is correct.")
        exit() # Exit if data file is not found

    # Generate and save Time Series plot
    fig_time_series = generate_time_series_plots(df_sample)
    time_series_filename = "time_series_plot.html"
    time_series_full_path = os.path.join(plot_save_dir, time_series_filename)
    fig_time_series.write_html(time_series_full_path)
    print(f"Time series plot saved to {time_series_full_path}")

    # Generate and save Product Sum plot
    fig_product_sum = generate_product_sum_plot(df_sample)
    product_sum_filename = "product_sum_plot.html"
    product_sum_full_path = os.path.join(plot_save_dir, product_sum_filename)
    fig_product_sum.write_html(product_sum_full_path)
    print(f"Product sum plot saved to {product_sum_full_path}")

    # Information for updating index.html
    plots_to_add = [
        {
            "name": "Time Series by Pillar",
            "filename": time_series_filename,
            "type_text": "Time Series", # Text for the span
            "type_class": "time-series" # CSS class for styling
        },
        {
            "name": "Product Sum",
            "filename": product_sum_filename,
            "type_text": "Time Series",
            "type_class": "time-series"
        }
    ]
    
    # Update index.html
    # index.html is assumed to be at "output/index.html" relative to script execution
    # The href paths for plots will be "Custom plot/filename.html"
    update_index_html(
        plot_info_list=plots_to_add,
        index_path="output/index.html",
        output_plot_dir="Custom plot" 
    )