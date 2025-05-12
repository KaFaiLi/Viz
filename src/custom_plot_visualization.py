import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import pandas as pd
import plotly.express as px
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

# --- Configuration for Multiple Datasets ---

# Define mapping configurations
MAPPING_CONFIG_SET1 = {
    'bond': ['bond', 'xone_bond', 'slbond'],
    'future': ['bondfuture', 'xone_bondfuture'],
    'irdswap': ['irdswap', 'xone_irdswap'],
    'repo': ['repo']
}

# Reordered to check more specific patterns first
MAPPING_CONFIG_SET2 = {
    'future': ['bondfuture', 'xone_bondfuture'],
    'bond': ['bond', 'xone_bond']
}

# Define the list of datasets to process
DEFAULT_CSV_DATASETS = [
    {
        "id": "IR Delta",
        "csv_path_relative": os.path.join("Input", "IR Delta 2023-20250314.csv"),
        "mapping_config": MAPPING_CONFIG_SET1
    },
    {
        "id": "FTQ",
        "csv_path_relative": os.path.join("Input", "FTQ 2023-20250314.csv"),
        "mapping_config": MAPPING_CONFIG_SET2
    }
]

# --- End Configuration ---

def load_and_preprocess_csv(csv_path: str, mapping_config: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Load and preprocess the CSV file with validation using specific mapping rules.

    Args:
        csv_path: Path to the CSV file
        mapping_config: Dictionary defining product category mappings {category: [patterns]}

    Returns:
        pd.DataFrame: Preprocessed dataframe

    Raises:
        ValueError: If required columns are missing or file not found
        FileNotFoundError: If the csv_path does not exist.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    required_columns = [
        "Global Product Name",
        "Projected Pillar",
        "pricingdate",
        "Validated Value Projected CV"
    ]

    try:
        df = pd.read_csv(csv_path)

        # Validate columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {csv_path}: {', '.join(missing_cols)}")

        # Parse pricingdate
        df['pricingdate'] = pd.to_datetime(df['pricingdate'])

        # Function to map product name to category based on provided config
        def get_product_category(product_name: str) -> str:
            if not isinstance(product_name, str):
                 # Handle potential non-string data if necessary
                 return 'other'
            
            product_name_lower = product_name.strip().lower() # Add strip() to handle whitespace
            
            for category, patterns in mapping_config.items():
                # Ensure patterns are lowercase for comparison
                if any(pattern.lower() in product_name_lower for pattern in patterns):
                    return category
                    
            return 'other' # Assign to 'other' if no match found

        # Add Product Category column
        df['Product Category'] = df['Global Product Name'].apply(get_product_category)

        logging.info(f"Successfully loaded and preprocessed {csv_path}")
        return df

    except Exception as e:
        # Catch pandas errors or other issues during processing
        logging.error(f"Error processing CSV file {csv_path}: {str(e)}")
        # Re-raise the exception to be caught by the caller
        raise Exception(f"Error processing CSV file {csv_path}: {str(e)}")


def aggregate_data(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Aggregate data by different groupings.

    Args:
        df: Input dataframe

    Returns:
        Dict containing different aggregated dataframes ('by_category', 'overall')
    """
    try:
        # Aggregate by Product Category
        by_category = df.groupby(
            ['pricingdate', 'Projected Pillar', 'Product Category']
        )['Validated Value Projected CV'].sum().reset_index()

        # Aggregate overall (ignoring Product Category)
        overall = df.groupby(
            ['pricingdate', 'Projected Pillar']
        )['Validated Value Projected CV'].sum().reset_index()

        return {
            'by_category': by_category,
            'overall': overall
        }
    except KeyError as e:
        logging.error(f"Aggregation failed: Missing expected column - {e}")
        raise # Propagate error
    except Exception as e:
        logging.error(f"Unexpected error during data aggregation: {e}")
        raise # Propagate error


def create_category_plots(df: pd.DataFrame, output_dir: str, dataset_id: str) -> List[str]:
    """
    Create time series subplot grids for each Product Category, one subplot per Projected Pillar.
    Filenames include the dataset_id.

    Args:
        df: Aggregated dataframe with category data
        output_dir: Directory to save the plots
        dataset_id: Identifier for the dataset (e.g., 'Set1')

    Returns:
        List of generated plot file paths
    """
    plot_files = []
    unique_categories = df['Product Category'].unique()
    logging.info(f"Creating category plots for {dataset_id}. Categories: {unique_categories}")

    for category in unique_categories:
        try:
            category_data = df[df['Product Category'] == category]
            if category_data.empty:
                logging.warning(f"No data for category '{category}' in dataset '{dataset_id}'. Skipping plot.")
                continue

            pillars = sorted(category_data['Projected Pillar'].unique())
            num_pillars = len(pillars)
            if num_pillars == 0:
                logging.warning(f"No pillars found for category '{category}' in dataset '{dataset_id}'. Skipping plot.")
                continue

            num_cols = 2
            num_rows = (num_pillars + num_cols -1) // num_cols # Ceiling division

            # Adjust layout calculations based on SGMR visualizer logic
            vertical_spacing = min(0.2, 0.8 / (num_rows - 1) if num_rows > 1 else 0.2)
            height = max(450 * num_rows, 600) # Base height per row, min 600
            width = height * 2.5 # Width relative to height

            fig = make_subplots(
                rows=num_rows,
                cols=num_cols,
                subplot_titles=[str(p) for p in pillars], # Use pillar names as subplot titles
                vertical_spacing=vertical_spacing,
                horizontal_spacing=0.15,
                shared_xaxes=False # Keep x-axes independent
            )

            for idx, pillar in enumerate(pillars):
                row = (idx // num_cols) + 1
                col = (idx % num_cols) + 1
                pillar_data = category_data[category_data['Projected Pillar'] == pillar]

                if pillar_data.empty:
                     logging.warning(f"No data for pillar '{pillar}' in category '{category}', dataset '{dataset_id}'. Skipping trace.")
                     continue

                fig.add_trace(
                    go.Scatter(
                        x=pillar_data['pricingdate'],
                        y=pillar_data['Validated Value Projected CV'],
                        mode='lines+markers',
                        name=str(pillar), # Legend entry (though legend is hidden)
                        showlegend=False # Individual trace legends off
                    ),
                    row=row,
                    col=col
                )
                fig.update_xaxes(title_text="Date", row=row, col=col)
                fig.update_yaxes(title_text="Aggregated CV Value", row=row, col=col)

            # Update overall layout for the category plot
            fig.update_layout(
                title=f"{dataset_id} - {category.upper()} - Time Series by Projected Pillar",
                height=height,
                width=width,
                plot_bgcolor='white',
                template="plotly_white", # Consistent theme
                hovermode='x unified', # Improved hover experience
                title_x=0.5 # Center the main title
                # showlegend=True # Optionally show legend if needed later
            )
    
            # Include dataset_id in the filename
            output_file = os.path.join(output_dir, f'timeseries_{dataset_id}_{category}.html')
            fig.write_html(output_file)
            plot_files.append(output_file)
            logging.info(f"Generated category plot: {output_file}")

        except Exception as e:
            logging.error(f"Failed to create plot for category '{category}', dataset '{dataset_id}': {e}")
            # Continue to next category if one fails

    return plot_files


def create_overall_plot(df: pd.DataFrame, output_dir: str, dataset_id: str) -> Optional[str]:
    """
    Create overall time series plot ignoring Product Category, using subplots per Pillar.
    Filename includes the dataset_id.

    Args:
        df: Overall aggregated dataframe (grouped by date and pillar only)
        output_dir: Directory to save the plot
        dataset_id: Identifier for the dataset (e.g., 'Set1')

    Returns:
        Path to the generated plot file, or None if generation fails or no data.
    """
    try:
        pillars = sorted(df['Projected Pillar'].unique())
        num_pillars = len(pillars)
        if num_pillars == 0:
            logging.warning(f"No pillars found for overall plot in dataset '{dataset_id}'. Skipping.")
            return None

        num_cols = 2
        num_rows = (num_pillars + num_cols -1) // num_cols

        vertical_spacing = min(0.2, 0.8 / (num_rows - 1) if num_rows > 1 else 0.2)
        height = max(450 * num_rows, 600)
        width = height * 2.5

        fig = make_subplots(
            rows=num_rows,
            cols=num_cols,
            subplot_titles=[str(p) for p in pillars],
            vertical_spacing=vertical_spacing,
            horizontal_spacing=0.15,
            shared_xaxes=False
        )

        for idx, pillar in enumerate(pillars):
            row = (idx // num_cols) + 1
            col = (idx % num_cols) + 1
            pillar_data = df[df['Projected Pillar'] == pillar]

            if pillar_data.empty:
                logging.warning(f"No data for overall pillar '{pillar}', dataset '{dataset_id}'. Skipping trace.")
                continue

            fig.add_trace(
                go.Scatter(
                    x=pillar_data['pricingdate'],
                    y=pillar_data['Validated Value Projected CV'],
                    mode='lines+markers',
                    name=str(pillar),
                    showlegend=False
                ),
                row=row,
                col=col
            )
            fig.update_xaxes(title_text="Date", row=row, col=col)
            fig.update_yaxes(title_text="Aggregated CV Value", row=row, col=col)

        # Update overall layout
        fig.update_layout(
            title=f"{dataset_id} - Overall Time Series by Projected Pillar (All Categories)",
            height=height,
            width=width,
            plot_bgcolor='white',
            template="plotly_white",
            hovermode='x unified',
            title_x=0.5
        )

        # Include dataset_id in the filename
        output_file = os.path.join(output_dir, f'timeseries_{dataset_id}_overall.html')
        fig.write_html(output_file)
        logging.info(f"Generated overall plot: {output_file}")
        return output_file

    except Exception as e:
        logging.error(f"Failed to create overall plot for dataset '{dataset_id}': {e}")
        return None


def process_csv_visualizations(
    csv_path: str,
    mapping_config: Dict[str, List[str]],
    output_dir: str,
    dataset_id: str
) -> List[Dict[str, Any]]:
    """
    Process a single CSV file and create all its visualizations.

    Args:
        csv_path: Path to the input CSV file
        mapping_config: Mapping configuration for this dataset
        output_dir: Base directory to save the plots (dataset-specific subdir will be created)
        dataset_id: Identifier for the dataset (e.g., 'Set1')

    Returns:
        List of plot configurations for dashboard integration for this dataset.
    """
    plot_configs = []
    try:
        # Create a subdirectory for this dataset's plots
        dataset_output_dir = os.path.join(output_dir, dataset_id)
        os.makedirs(dataset_output_dir, exist_ok=True)
        logging.info(f"Output directory for {dataset_id}: {dataset_output_dir}")

        # Load and preprocess data using the specific mapping config
        df = load_and_preprocess_csv(csv_path, mapping_config)

        # Aggregate data
        aggregated_data = aggregate_data(df)

        # Create category plots (subplot grid per category)
        category_plot_files = create_category_plots(
            aggregated_data['by_category'],
            dataset_output_dir, # Save into dataset-specific subdir
            dataset_id
        )

        # Create overall plot (subplot grid)
        overall_plot_file = create_overall_plot(
            aggregated_data['overall'],
            dataset_output_dir, # Save into dataset-specific subdir
            dataset_id
        )
    
        # Prepare plot configurations for dashboard
        # Add category plots
        for plot_file in category_plot_files:
            # Extract category from filename (e.g., timeseries_Set1_bond.html -> bond)
            try:
                base_name = os.path.splitext(os.path.basename(plot_file))[0]
                # Handle potential variations if filename format changes
                parts = base_name.split('_')
                if len(parts) >= 3:
                     category = parts[2] # Assumes format timeseries_DATASETID_CATEGORY
                else:
                     category = "Unknown" # Fallback
                plot_configs.append({
                    "plot_html_file": plot_file, # Full path to the plot in the subdir
                    "metric_type": f"{dataset_id} Time Series", # Include dataset ID
                    "metric_name": f"CV Values - {category.upper()}" # Keep category name
                })
            except Exception as e:
                 logging.error(f"Error parsing category filename {plot_file}: {e}")


        # Add overall plot if generated successfully
        if overall_plot_file:
            plot_configs.append({
                "plot_html_file": overall_plot_file, # Full path
                "metric_type": f"{dataset_id} Time Series", # Include dataset ID
                "metric_name": "CV Values - Overall"
            })

        logging.info(f"Finished processing visualizations for dataset {dataset_id} from {csv_path}")

    except FileNotFoundError as e:
        logging.error(f"Skipping dataset {dataset_id}: Input CSV file not found at {csv_path}. Error: {e}")
    except ValueError as e:
        logging.error(f"Skipping dataset {dataset_id}: Data validation error in {csv_path}. Error: {e}")
    except Exception as e:
        # Catch-all for other errors during processing of this specific dataset
        logging.error(f"Failed to process dataset {dataset_id} from {csv_path}: {e}")

    return plot_configs


# --- HTML Dashboard Update Function (Modified for Clarity) ---
def update_main_html(main_html_file, plot_configurations_list):
    """Update the main HTML dashboard to include multiple custom visualizations under a single section."""
    logging.info(f"Attempting to update main dashboard: {main_html_file}")
    try:
        with open(main_html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        logging.info(f"Successfully read existing dashboard file.")
    except FileNotFoundError:
        logging.warning(f"Main HTML file '{main_html_file}' not found. A template will be created.")
        # Create a basic HTML structure if the file doesn't exist.
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
        logging.info(f"Created new dashboard template file at {main_html_file}")

    all_metric_cards_html = ""
    main_html_dir = os.path.dirname(main_html_file)

    if not plot_configurations_list:
        logging.warning("No plot configurations provided to update_main_html. Dashboard section will be empty.")
        all_metric_cards_html = "<p>No custom plots generated.</p>"
    else:
        logging.info(f"Generating {len(plot_configurations_list)} metric cards for the dashboard.")
        for plot_config in plot_configurations_list:
            try:
                # Calculate relative path from main HTML file dir to plot file
                # Ensure plot_html_file is an absolute path for relpath
                plot_html_abs_path = os.path.abspath(plot_config["plot_html_file"])
                relative_plot_path = os.path.relpath(plot_html_abs_path, main_html_dir)
                # Use forward slashes for web compatibility
                relative_plot_path = relative_plot_path.replace(os.sep, '/')
        
                metric_card_html = f'''
                    <div class="metric-card">
                        <span class="metric-type time-series">{plot_config.get("metric_type", "Plot")}</span>
                        <span class="metric-name">{plot_config.get("metric_name", "Unnamed Plot")}</span>
                        <a href="{relative_plot_path}" target="_blank" aria-label="View {plot_config.get("metric_name", "Unnamed Plot")}"></a>
                    </div>'''
                all_metric_cards_html += metric_card_html
            except KeyError as e:
                logging.error(f"Skipping plot config due to missing key: {e}. Config: {plot_config}")
            except Exception as e:
                 logging.error(f"Error generating metric card for {plot_config.get('plot_html_file', 'N/A')}: {e}")


    # --- Create/Update the 'Custom Plots' section ---
    section_start_tag = '<!-- BEGIN CUSTOM PLOTS SECTION -->'
    section_end_tag = '<!-- END CUSTOM PLOTS SECTION -->'
    section_title = "Custom Plots" # Title for the section

    # New HTML content for the section
    new_section_content = f'''
{section_start_tag}
    <section class="node-section">
    <h2>{section_title}</h2>
        <div class="metrics-grid">
            {all_metric_cards_html}
        </div>
    </section>
{section_end_tag}
    '''
    
    # Check if the section already exists
    start_index = content.find(section_start_tag)
    end_index = content.find(section_end_tag)

    if start_index != -1 and end_index != -1:
        # Section exists, replace its content
        logging.info("Found existing 'Custom Plots' section. Replacing content.")
        # Ensure end_index points to the end of the closing tag
        end_index += len(section_end_tag)
        # Replace the old section with the new content
        content = content[:start_index] + new_section_content + content[end_index:]
    else:
        # Section doesn't exist, insert it before the closing body tag
        logging.info("Existing 'Custom Plots' section not found. Inserting new section.")
    if '</body>' in content:
            content = content.replace('</body>', f'{new_section_content}</body>', 1)
    else:
        # If no body tag, append (basic fallback)
            logging.warning("No </body> tag found. Appending section to the end of the file.")
            content += new_section_content

    try:
        with open(main_html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Main HTML file '{main_html_file}' updated successfully.")
    except Exception as e:
        logging.error(f"Failed to write updated content to {main_html_file}: {e}")


# --- Main Execution Function (Modified) ---
def run_all_custom_visualizations():
    """
    Generates CSV-based custom plots and updates the main dashboard HTML.
    Processes datasets defined in DEFAULT_CSV_DATASETS.
    (Hardcoded plots removed).
    """
    logging.info("Starting execution of run_all_custom_visualizations (CSV plots only)...")
    # Get script's directory and workspace root
    script_path_abspath = os.path.abspath(__file__)
    src_dir = os.path.dirname(script_path_abspath)
    workspace_root = os.path.dirname(src_dir)
    logging.info(f"Workspace root determined as: {workspace_root}")

    # Set up output directories
    output_dir = os.path.join(workspace_root, "output")
    # Base directory for all custom plots
    custom_plot_base_dir = os.path.join(output_dir, "Custom_Plots") # Base directory for CSV plots

    # Ensure the base custom plot output directory exists
    os.makedirs(custom_plot_base_dir, exist_ok=True)
    logging.info(f"Ensured base output directory exists: {custom_plot_base_dir}")
    
    main_dashboard_html_file = os.path.join(output_dir, "index.html")
    logging.info(f"Main dashboard HTML file path: {main_dashboard_html_file}")

    # List to hold configurations for ALL CSV plots from all datasets
    all_plot_configs = []

    # --- Process CSV Datasets ---
    logging.info(f"Processing {len(DEFAULT_CSV_DATASETS)} CSV datasets...")
    for dataset_config in DEFAULT_CSV_DATASETS:
        dataset_id = dataset_config["id"]
        relative_path = dataset_config["csv_path_relative"]
        mapping_config = dataset_config["mapping_config"]
        absolute_csv_path = os.path.join(workspace_root, relative_path)

        logging.info(f"--- Processing Dataset: {dataset_id} ---")
        logging.info(f"CSV Path: {absolute_csv_path}")

        # Call processing function for this dataset
        csv_plot_configs = process_csv_visualizations(
            csv_path=absolute_csv_path,
            mapping_config=mapping_config,
            output_dir=custom_plot_base_dir, # Pass base dir
            dataset_id=dataset_id
        )
        # Add the generated plot configs for this dataset to the main list
        all_plot_configs.extend(csv_plot_configs)
        logging.info(f"--- Finished Dataset: {dataset_id} ---")
    
    # --- Update Main HTML with CSV plots only ---
    logging.info(f"Updating main dashboard ({main_dashboard_html_file}) with {len(all_plot_configs)} CSV plot entries.")
    update_main_html(
        main_html_file=main_dashboard_html_file,
        plot_configurations_list=all_plot_configs # Pass the list containing only CSV plot configs
    )

    # Final Summary Output (Modified)
    print("\n--- Custom Plot Generation Summary ---")
    # Removed listing of hardcoded plots

    # List CSV plots generated
    csv_plots_generated = all_plot_configs # Simpler check now
    if csv_plots_generated:
        print(f"1. CSV-based plots generated in subdirectories within: {custom_plot_base_dir}")
        # Optionally list individual CSV plots or datasets processed
        processed_ids = sorted(list(set(cfg['id'] for cfg in DEFAULT_CSV_DATASETS if os.path.exists(os.path.join(workspace_root, cfg['csv_path_relative']))))) # Check if file exists before listing ID
        if processed_ids:
             print(f"   (Successfully processed datasets: {', '.join(processed_ids)})")
        else:
             print("   (No CSV datasets were successfully processed)")
    else:
        print("1. No CSV-based plots were generated.")


    print(f"2. Main dashboard updated at: {main_dashboard_html_file}")
    print("   Open the dashboard in your browser to see the changes.")
    logging.info("--- run_all_custom_visualizations finished ---")