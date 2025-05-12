"""Module for handling visualization configuration."""

from typing import Dict, List, TypedDict

class MetricConfig(TypedDict):
    mother_metrics: List[str]
    plot_types: List[str]

class NodeConfig(TypedDict):
    metrics_config: List[MetricConfig]

class VisualizationConfig:
    """Configuration for visualization settings."""
    
    @staticmethod
    def get_default_config() -> Dict[str, NodeConfig]:
        """
        Get the default visualization configuration.
        
        Returns:
            Dict containing the visualization configuration for each node
        """
        return {
            'FICRATG10JGB': {
                'metrics_config': [
                    {
                        'mother_metrics': [
                            'CredBpv', 'BASISSensiByCurrencyByPillar',
                            'FX', 'FXUSD', 'FXEUR', 'FXJPY',
                            'FTQ', 'FTQglobJapan',
                        ],
                        'plot_types': ['bar']
                    },
                    {
                        'mother_metrics': [
                            'SOVFuture', 'CredBpv', 'BASISSensiByCurrencyByPillar',
                            'FX', 'FXUSD', 'FXEUR', 'FXJPY',
                            'FTQglobJapan', 'FTQglobJapan1M',
                        ],
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

    @staticmethod
    def validate_config(config: Dict[str, NodeConfig]) -> bool:
        """
        Validate the configuration format.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        valid_plot_types = {'bar', 'time_series'}
        
        for node, node_config in config.items():
            if not isinstance(node_config, dict):
                raise ValueError(f"Invalid configuration for node {node}")
                
            if 'metrics_config' not in node_config:
                raise ValueError(f"Missing metrics_config for node {node}")
                
            for metric_config in node_config['metrics_config']:
                if not isinstance(metric_config, dict):
                    raise ValueError(f"Invalid metric configuration in node {node}")
                    
                if 'mother_metrics' not in metric_config or 'plot_types' not in metric_config:
                    raise ValueError(f"Missing required fields in metric configuration for node {node}")
                    
                if not isinstance(metric_config['mother_metrics'], list):
                    raise ValueError(f"mother_metrics must be a list in node {node}")
                    
                if not isinstance(metric_config['plot_types'], list):
                    raise ValueError(f"plot_types must be a list in node {node}")
                    
                invalid_plot_types = set(metric_config['plot_types']) - valid_plot_types
                if invalid_plot_types:
                    raise ValueError(f"Invalid plot types in node {node}: {invalid_plot_types}")
        
        return True 