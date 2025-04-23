import os
from pathlib import Path
from typing import Dict, List
from src.data_loader import DataLoader
from src.data_visualizer import DataVisualizer

def main():
    # Initialize data loader and load data
    data_loader = DataLoader()
    data = data_loader.load_csv('Input/fake_data.csv')
    
    # Initialize visualizer
    visualizer = DataVisualizer(data)
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Define visualization preferences for each stranaNode
    visualization_config = {
        'FICRATG10JGB': {
            'metrics_config': [
                {
                    'mother_metrics': ['CredBpv'],
                    'plot_types': ['bar']
                },
                {
                    'mother_metrics': ['SOVFuture'],
                    'plot_types': ['time_series']
                }
            ]
        },
        'FICASIRATFLO': {
            'metrics_config': [
                {
                    'mother_metrics': ['VaR'],
                    'plot_types': ['time_series']
                }
            ]
        }
    }
    
    # Process each stranaNode
    for strana_node, config in visualization_config.items():
        # Process each metric configuration for this stranaNode
        for metric_config in config['metrics_config']:
            mother_metrics = metric_config['mother_metrics']
            plot_types = metric_config['plot_types']
            
            # Create grouped bar plots if requested
            if 'bar' in plot_types and mother_metrics:
                output_file = f'output/{strana_node}_{"_".join(mother_metrics)}_bar.html'
                visualizer.create_grouped_bar_plots(
                    strana_node=strana_node,
                    mother_metrics=mother_metrics,
                    output_file=output_file
                )
            
            # Create time series plots
            if 'time_series' in plot_types:
                for metric in mother_metrics:
                    output_file = f'output/{strana_node}_{metric}_timeseries.html'
                    visualizer.create_time_series_plot(
                        strana_node=strana_node,
                        mother_metric=metric,
                        output_file=output_file
                    )

if __name__ == '__main__':
    main() 