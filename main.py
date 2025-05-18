"""Main script for generating risk metric visualizations."""

import os
import logging
from pathlib import Path
import sys
from datetime import datetime
from typing import Optional, Union, List
import pandas as pd
import time
import concurrent.futures

# Add src directory to Python path to allow direct import
# This assumes main.py is in the projenct root and custom_plot_visualization.py is in src/
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_root, 'src'))

try:
    from src.custom_plot_visualization import run_all_custom_visualizations
except ImportError as e:
    print(f"Error importing custom_plot_visualization: {e}")
    print("Please ensure custom_plot_visualization.py is in the 'src' directory and src is in PYTHONPATH.")
    sys.exit(1)

from src.utils import DataLoader
from src.SGMR_visualizer import DataVisualizer
from src.html_generator import HTMLGenerator
from src.config import VisualizationConfig
from src.pnl_visualization import create_pnl_visualization

# Cache for loaded event dates to avoid repeated file reads
_EVENT_DATES_CACHE = None

# Concurrency utilities
from concurrent.futures import ProcessPoolExecutor, as_completed

def setup_logging():
    """Configure logging settings."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def create_output_directories(config: dict) -> None:
    """
    Create output directories for each node.
    
    Args:
        config: Visualization configuration dictionary
    """
    for node in config.keys():
        node_output_dir = Path('output') / node
        os.makedirs(node_output_dir, exist_ok=True)
        logging.info(f"Created output directory: {node_output_dir}")

def load_event_dates() -> List[datetime]:
    """
    Load event dates from the Auction Date CSV file.
    Uses caching to avoid repeated file reads.
    
    Returns:
        List[datetime]: List of event dates
    """
    global _EVENT_DATES_CACHE
    
    if _EVENT_DATES_CACHE is not None:
        return _EVENT_DATES_CACHE
    
    try:
        auction_date_file = Path('Input') / 'Auction Date.csv'
        if not auction_date_file.exists():
            logging.warning(f"Auction Date file not found at {auction_date_file}. Using default dates.")
            return [datetime(2023, 3, 14), datetime(2023, 3, 16)]
        
        df = pd.read_csv(auction_date_file)
        if 'EventDate' not in df.columns:
            logging.warning("EventDate column not found in Auction Date file. Using default dates.")
            return [datetime(2023, 3, 14), datetime(2023, 3, 16)]
        
        # Convert string dates to datetime objects
        event_dates = [pd.to_datetime(date_str).to_pydatetime() for date_str in df['EventDate']]
        
        # Sort dates for consistency
        event_dates.sort()
        
        # Cache for future use
        _EVENT_DATES_CACHE = event_dates
        
        logging.info(f"Loaded {len(event_dates)} event dates from {auction_date_file}")
        return event_dates
    
    except Exception as e:
        logging.error(f"Error loading event dates from Auction Date file: {e}")
        return [datetime(2023, 3, 14), datetime(2023, 3, 16)]

def process_plots(
    visualizer: DataVisualizer,
    config: dict,
    plot_files_info: list
) -> None:
    """
    Process and generate all plots based on configuration.
    
    Args:
        visualizer: DataVisualizer instance
        config: Visualization configuration dictionary
        plot_files_info: List to store plot information
    """
    # Load event dates once for all plots
    event_dates = load_event_dates()
    
    # Track total plot generation time for reporting
    start_time = time.time()
    total_plots = 0
    
    for strana_node, node_config in config.items():
        logging.info(f"Processing stranaNode: {strana_node}")
        node_output_dir = Path('output') / strana_node

        for metric_config in node_config['metrics_config']:
            mother_metrics = metric_config['mother_metrics']
            plot_types = metric_config['plot_types']
            
            # Create grouped bar plots if requested
            if 'bar' in plot_types and mother_metrics:
                # Define the specific dates for the bar plot
                dates_for_bar_plot = [
                    datetime(2023, 3, 14),
                    datetime(2023, 3, 16),
                    datetime(2023, 3, 18)
                ]
                create_bar_plot(
                    visualizer, strana_node, mother_metrics,
                    node_output_dir, plot_files_info,
                    selected_dates=dates_for_bar_plot
                )
                total_plots += 1
            
            # Create time series plots
            if 'time_series' in plot_types:
                create_time_series_plots(
                    visualizer, config, strana_node, mother_metrics,
                    node_output_dir, plot_files_info,
                    event_dates=event_dates
                )
                total_plots += 1
    
    elapsed_time = time.time() - start_time
    logging.info(f"Generated {total_plots} plots in {elapsed_time:.2f} seconds")

def create_bar_plot(
    visualizer: DataVisualizer,
    strana_node: str,
    mother_metrics: list,
    output_dir: Path,
    plot_files_info: list,
    selected_dates: Optional[Union[datetime, List[datetime]]] = None
) -> None:
    """Create a grouped bar plot for the specified metrics."""
    # Create a unique filename part if multiple dates are selected
    date_suffix = ""
    if isinstance(selected_dates, list) and len(selected_dates) > 1:
        # Use a generic suffix or hash if list is too long to put in filename
        date_suffix = "_multi_date" 
    elif isinstance(selected_dates, datetime):
        date_suffix = f"_{selected_dates.strftime('%Y%m%d')}"
    # else, if selected_dates is None or a list with one date, the visualizer handles latest date,
    # or the single date might be incorporated differently by visualizer if needed.
    # For now, the original filename logic for single/latest date is implicitly handled by visualizer.

    # Simplified filename logic
    if len(mother_metrics) == 1:
        metrics_name_part = mother_metrics[0]  # Use the single metric name
    elif len(mother_metrics) > 1:
        metrics_name_part = "multiple_metrics" # Generic name for multiple metrics
    else: # Should not happen based on current call structure in process_plots, but good to be defensive
        metrics_name_part = "metrics" # Default if mother_metrics is unexpectedly empty

    output_filename = f'{strana_node}_{metrics_name_part}_bar{date_suffix}.html'
    output_file_path = output_dir / output_filename
    
    logging.info(f"Creating grouped bar plot for {strana_node}, "
                f"metrics: {', '.join(mother_metrics)}. "
                f"Output: {output_file_path}")
    
    try:
        visualizer.create_grouped_bar_plots(
            strana_node=strana_node,
            mother_metrics=mother_metrics,
            selected_dates=selected_dates,
            output_file=str(output_file_path)
        )
        plot_files_info.append({
            'strana_node': strana_node,
            'plot_type': 'bar',
            'metrics': mother_metrics,
            'output_file': str(output_file_path)
        })
        logging.info("Grouped bar plot created.")
    except Exception as e:
        logging.error(f"Error creating grouped bar plot for {strana_node} - "
                     f"metrics {mother_metrics}: {e}")

def generate_single_time_series_plot(metric_name, strana_node, data_slice, output_file_path_local, event_dates):
    # Log start of processing within the worker
    logging.info(f"[Worker] Starting plot generation for metric: {metric_name}, node: {strana_node}")

    visualizer_local = DataVisualizer(data_slice)
    logging.basicConfig(level=logging.INFO)
    visualizer_local.create_time_series_plot(
        strana_node=strana_node,
        mother_metric=metric_name,
        output_file=output_file_path_local,
        event_dates=event_dates
    )
    return {
        'strana_node': strana_node,
        'plot_type': 'time_series',
        'metrics': metric_name,
        'output_file': output_file_path_local
    }

def create_time_series_plots(
    visualizer: DataVisualizer,
    config: dict,
    strana_node: str,
    mother_metrics: list,
    output_dir: Path,
    plot_files_info: list,
    event_dates: Optional[List[datetime]] = None
) -> None:
    """Create time series plots for the specified metrics using parallel processes."""

    import pandas as pd
    # We'll extract the full data DataFrame from the visualizer.
    full_data = visualizer.data.copy()

    max_workers = min(16, max(1, len(mother_metrics)))
    futures = []
    # Keep track of which future belongs to which metric for better logging
    future_to_metric = {}

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for metric in mother_metrics:
            output_filename_local = f'{strana_node}_{metric}_timeseries.html'
            output_file_path_local = str(output_dir / output_filename_local)
            # Filter only the relevant data for this metric and strana_node
            mask = (full_data['stranaNodeName'] == strana_node)
            data_slice = full_data[mask].copy()
            # Pass only the data for this strana_node (DataVisualizer will further filter by metric)
            future = executor.submit(generate_single_time_series_plot, metric, strana_node, data_slice, output_file_path_local, event_dates)
            futures.append(future)
            future_to_metric[future] = metric

        pending_futures = set(futures)
        last_status_time = time.time()

        while pending_futures:
            # Wait for at least one future to complete, or timeout after 60 seconds
            done, pending_futures = concurrent.futures.wait(
                pending_futures, 
                timeout=60, 
                return_when=concurrent.futures.FIRST_COMPLETED
            )

            # Process completed futures
            for fut in done:
                metric = future_to_metric[fut]
                try:
                    info = fut.result() # Get result or raise exception
                    plot_files_info.append(info)
                    logging.info(
                        f"[ProcessPool] Successfully completed plot for metric: {metric}"
                    )
                except Exception as e:
                    logging.error(
                        f"[ProcessPool] Error generating plot for metric {metric}, node {strana_node}: {e}"
                    )
                # Remove from tracking dictionary (optional)
                del future_to_metric[fut]

            # Periodic status update (every ~60 seconds based on timeout)
            current_time = time.time()
            if current_time - last_status_time >= 60 or not pending_futures:
                if pending_futures:
                    pending_metrics = [future_to_metric[f] for f in pending_futures]
                    logging.info(f"[Status] {len(futures) - len(pending_futures)}/{len(futures)} plots completed. Still pending: {pending_metrics}")
                else:
                    logging.info("[Status] All time series plots processed.")
                last_status_time = current_time

def main():
    """Main function to run the visualization script, with option to skip time series if already done."""
    setup_logging()
    logging.info("Starting the visualization script.")

    # Marker file to indicate time series plots are done
    timeseries_marker = Path('output') / 'timeseries_done.marker'

    try:
        # Load configuration
        config = VisualizationConfig.get_default_config()
        VisualizationConfig.validate_config(config)

        # Initialize data loader and load data
        logging.info("Initializing DataLoader.")
        data_loader = DataLoader()
        logging.info("Loading data from Input/fake_data.csv.")
        data = data_loader.load_csv('Input/fake_data.csv')
        logging.info("Data loaded successfully.")

        # Initialize visualizer
        logging.info("Initializing DataVisualizer.")
        visualizer = DataVisualizer(data)

        # Create output directories
        create_output_directories(config)

        # Decide whether to run time series plots
        skip_timeseries = False
        if timeseries_marker.exists():
            user_input = input("Time series plots have already been generated. Skip time series and only run other visualizations? (y/n): ").strip().lower()
            if user_input == 'y':
                skip_timeseries = True

        plot_files_info = []
        if not skip_timeseries:
            process_plots(visualizer, config, plot_files_info)
            # Write marker file to indicate time series are done
            timeseries_marker.parent.mkdir(parents=True, exist_ok=True)
            with open(timeseries_marker, 'w') as f:
                f.write('done')
        else:
            logging.info("Skipping time series plot generation as per user request.")

        # Generate PNL Attribution visualization
        logging.info("Generating PNL Attribution visualization.")
        try:
            pnl_vis_file = create_pnl_visualization()
            logging.info(f"PNL Attribution visualization created successfully: {pnl_vis_file}")
        except Exception as e:
            logging.error(f"Error creating PNL Attribution visualization: {e}")

        # Generate the index HTML file
        HTMLGenerator.generate_index_html(plot_files_info, Path('output'))

        logging.info("Visualization script finished successfully.")

    except Exception as e:
        logging.error(f"Error running visualization script: {e}")
        raise

    print("Starting main application...")

    # Call the function from custom_plot_visualization.py
    print("Generating custom plots and updating dashboard...")
    try:
        run_all_custom_visualizations()
        print("Custom plot generation process completed by custom_plot_visualization module.")
    except Exception as e:
        print(f"An error occurred while running custom visualizations: {e}")

    print("Main application finished.")

if __name__ == '__main__':
    main() 