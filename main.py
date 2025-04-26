"""Main script for generating risk metric visualizations."""

import os
import logging
from pathlib import Path

from src.data_loader import DataLoader
from src.data_visualizer import DataVisualizer
from src.html_generator import HTMLGenerator
from src.config import VisualizationConfig
from src.pnl_visualization import create_pnl_visualization

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
    for strana_node, node_config in config.items():
        logging.info(f"Processing stranaNode: {strana_node}")
        node_output_dir = Path('output') / strana_node

        for metric_config in node_config['metrics_config']:
            mother_metrics = metric_config['mother_metrics']
            plot_types = metric_config['plot_types']
            
            # Create grouped bar plots if requested
            if 'bar' in plot_types and mother_metrics:
                create_bar_plot(
                    visualizer, strana_node, mother_metrics,
                    node_output_dir, plot_files_info
                )
            
            # Create time series plots
            if 'time_series' in plot_types:
                create_time_series_plots(
                    visualizer, strana_node, mother_metrics,
                    node_output_dir, plot_files_info
                )

def create_bar_plot(
    visualizer: DataVisualizer,
    strana_node: str,
    mother_metrics: list,
    output_dir: Path,
    plot_files_info: list
) -> None:
    """Create a grouped bar plot for the specified metrics."""
    output_filename = f'{strana_node}_{"_".join(mother_metrics)}_bar.html'
    output_file_path = output_dir / output_filename
    
    logging.info(f"Creating grouped bar plot for {strana_node}, "
                f"metrics: {', '.join(mother_metrics)}. "
                f"Output: {output_file_path}")
    
    try:
        visualizer.create_grouped_bar_plots(
            strana_node=strana_node,
            mother_metrics=mother_metrics,
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

def create_time_series_plots(
    visualizer: DataVisualizer,
    strana_node: str,
    mother_metrics: list,
    output_dir: Path,
    plot_files_info: list
) -> None:
    """Create time series plots for the specified metrics."""
    for metric in mother_metrics:
        output_filename = f'{strana_node}_{metric}_timeseries.html'
        output_file_path = output_dir / output_filename
        
        logging.info(f"Creating time series plot for {strana_node}, "
                    f"metric: {metric}. Output: {output_file_path}")
        
        try:
            visualizer.create_time_series_plot(
                strana_node=strana_node,
                mother_metric=metric,
                output_file=str(output_file_path)
            )
            plot_files_info.append({
                'strana_node': strana_node,
                'plot_type': 'time_series',
                'metrics': metric,
                'output_file': str(output_file_path)
            })
            logging.info(f"Time series plot for metric {metric} created.")
        except Exception as e:
            logging.error(f"Error creating time series plot for {strana_node} - "
                         f"metric {metric}: {e}")

def main():
    """Main function to run the visualization script."""
    # Setup logging
    setup_logging()
    logging.info("Starting the visualization script.")

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
        
        # Process all plots
        plot_files_info = []
        process_plots(visualizer, config, plot_files_info)

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

if __name__ == '__main__':
    main() 