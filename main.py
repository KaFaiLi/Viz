import os
from pathlib import Path
from typing import Dict, List
from src.data_loader import DataLoader
from src.data_visualizer import DataVisualizer

def main():
    # Initialize data loader
    loader = DataLoader()
    
    # Load data from CSV file
    try:
        data = loader.load_csv('Input/fake_data.csv')
        print("Data loaded successfully!")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return
    
    # Initialize visualizer
    visualizer = DataVisualizer(data)
    
    # Define visualization preferences
    # Format: {
    #     'strana_node': {
    #         'metrics': {
    #             'metric_name': ['bar', 'time_series'],  # or ['bar'] or ['time_series'] or []
    #         },
    #         'time_series_metrics': ['metric1', 'metric2']  # metrics to include in grouped time series
    #     }
    # }
    visualization_preferences = {
        # Example for FICRATG10JGB
        'FICRATG10JGB': {
            'metrics': {
                'CredBpv': ['bar', 'time_series'],  # Both bar and time series
                'CredBpv10Y': ['time_series'],      # Only time series
                'CredBpv3Y': ['bar'],              # Only bar plot
                'SOVFutureJapan': []               # Skip this metric
            },
            'time_series_metrics': ['CredBpv', 'CredBpv10Y']  # Group these in time series
        },
        
        # Example for another stranaNode
        'FICASIRATFLO': {
            'metrics': {
                'VaR': ['bar', 'time_series']
            },
            'time_series_metrics': ['VaR']
        }
        
        # Add more stranaNodes and their preferences as needed
    }
    
    # Create output directory for plots if it doesn't exist
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Create visualizations based on preferences
    for strana_node, node_prefs in visualization_preferences.items():
        print(f"\nProcessing {strana_node}...")
        
        # Create individual plots
        for metric, plot_types in node_prefs['metrics'].items():
            for plot_type in plot_types:
                try:
                    if plot_type == 'bar':
                        output_file = output_dir / f"{strana_node}_{metric}_bar.html"
                        fig = visualizer.create_bar_plot(
                            strana_node=strana_node,
                            metric_name=metric,
                            output_file=str(output_file)
                        )
                        print(f"Created bar plot: {output_file}")
                
                except Exception as e:
                    print(f"Error creating {plot_type} plot for {strana_node} - {metric}: {str(e)}")
        
        # Create grouped time series plot if there are any time series metrics for this node
        time_series_metrics = node_prefs['time_series_metrics']
        if time_series_metrics:
            try:
                output_file = output_dir / f"{strana_node}_grouped_timeseries.html"
                fig = visualizer.create_grouped_time_series_plot(
                    strana_node=strana_node,
                    metrics=time_series_metrics,
                    output_file=str(output_file)
                )
                print(f"Created grouped time series plot: {output_file}")
            except Exception as e:
                print(f"Error creating grouped time series plot for {strana_node}: {str(e)}")

if __name__ == "__main__":
    main() 