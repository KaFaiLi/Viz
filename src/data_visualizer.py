import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime

class DataVisualizer:
    def __init__(self, data: pd.DataFrame):
        """
        Initialize the DataVisualizer with a pandas DataFrame.
        
        Args:
            data (pd.DataFrame): Input DataFrame with the required columns
        """
        self.data = data.copy()
            
    def _extract_maturity(self, metric_name: str) -> Optional[str]:
        """Extract maturity from metric name if present."""
        # Common maturity patterns like 3M, 1Y, 2Y, etc.
        maturity_pattern = r'(\d+[DWMY])'
        match = re.search(maturity_pattern, metric_name)
        return match.group(1) if match else None
        
    def _extract_currency(self, metric_name: str) -> Optional[str]:
        """Extract currency from metric name if present."""
        # Match patterns like [USD], [EUR], [JPY]
        currency_pattern = r'\[([A-Z]{3})\]'
        match = re.search(currency_pattern, metric_name)
        return match.group(1) if match else None
    
    def get_available_strana_nodes(self) -> List[str]:
        """Return list of available stranaNodeName values."""
        return sorted(self.data['stranaNodeName'].unique())
    
    def get_metrics_for_node(self, strana_node: str) -> List[str]:
        """Return list of metrics available for a given stranaNodeName."""
        return sorted(self.data[self.data['stranaNodeName'] == strana_node]['rmRiskMetricName'].unique())
    
    def create_grouped_time_series_plot(
        self,
        strana_node: str,
        metrics: List[str],
        show_limits: bool = True,
        output_file: Optional[str] = None
    ) -> go.Figure:
        """
        Create a grouped time series plot for multiple metrics in the same stranaNode.
        
        Args:
            strana_node (str): The stranaNodeName to plot
            metrics (List[str]): List of rmRiskMetricNames to plot
            show_limits (bool): Whether to show limit lines if available
            output_file (str, optional): If provided, save the plot to this file
        
        Returns:
            go.Figure: Plotly figure object
        """
        # Create figure with secondary y-axis
        fig = make_subplots(
            rows=len(metrics),
            cols=1,
            subplot_titles=[f"{strana_node} - {metric}" for metric in metrics],
            vertical_spacing=0.1
        )
        
        for idx, metric_name in enumerate(metrics, 1):
            # Filter data
            mask = (self.data['stranaNodeName'] == strana_node) & \
                   (self.data['rmRiskMetricName'] == metric_name)
            plot_data = self.data[mask].copy()
            
            # Group by consoMreMetricName to plot each series
            for metric in plot_data['consoMreMetricName'].unique():
                metric_data = plot_data[plot_data['consoMreMetricName'] == metric]
                metric_data = metric_data.sort_values('Date')
                
                fig.add_trace(
                    go.Scatter(
                        x=metric_data['Date'],
                        y=metric_data['consoValue'],
                        name=metric,
                        mode='lines+markers'
                    ),
                    row=idx,
                    col=1
                )
            
            # Add limit lines if they exist and are requested
            if show_limits:
                latest_data = plot_data.iloc[-1] if not plot_data.empty else None
                if latest_data is not None:
                    if pd.notna(latest_data['limMaxValue']):
                        fig.add_hline(
                            y=latest_data['limMaxValue'],
                            line_dash="dash",
                            line_color="red",
                            annotation_text="Max Limit",
                            row=idx,
                            col=1
                        )
                    if pd.notna(latest_data['limMinValue']):
                        fig.add_hline(
                            y=latest_data['limMinValue'],
                            line_dash="dash",
                            line_color="red",
                            annotation_text="Min Limit",
                            row=idx,
                            col=1
                        )
        
        # Update layout
        height = max(300 * len(metrics), 600)  # Minimum height of 600px
        fig.update_layout(
            height=height,
            showlegend=True,
            template="plotly_white",
            title=f"Time Series for {strana_node}"
        )
        
        if output_file:
            fig.write_html(output_file)
            
        return fig
    
    def create_time_series_plot(
        self,
        strana_node: str,
        metric_name: str,
        show_limits: bool = True,
        output_file: Optional[str] = None
    ) -> go.Figure:
        """
        Create a time series plot for the specified stranaNode and metric.
        
        Args:
            strana_node (str): The stranaNodeName to plot
            metric_name (str): The rmRiskMetricName to plot
            show_limits (bool): Whether to show limit lines if available
            output_file (str, optional): If provided, save the plot to this file
        
        Returns:
            go.Figure: Plotly figure object
        """
        # Filter data
        mask = (self.data['stranaNodeName'] == strana_node) & \
               (self.data['rmRiskMetricName'] == metric_name)
        plot_data = self.data[mask].copy()
        
        # Create figure
        fig = go.Figure()
        
        # Group by consoMreMetricName to plot each series
        for metric in plot_data['consoMreMetricName'].unique():
            metric_data = plot_data[plot_data['consoMreMetricName'] == metric]
            
            # Sort by date
            metric_data = metric_data.sort_values('Date')
            
            fig.add_trace(go.Scatter(
                x=metric_data['Date'],
                y=metric_data['consoValue'],
                name=metric,
                mode='lines+markers'
            ))
        
        # Add limit lines if they exist and are requested
        if show_limits:
            latest_data = plot_data.iloc[-1]
            if pd.notna(latest_data['limMaxValue']):
                fig.add_hline(
                    y=latest_data['limMaxValue'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Max Limit"
                )
            if pd.notna(latest_data['limMinValue']):
                fig.add_hline(
                    y=latest_data['limMinValue'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Min Limit"
                )
        
        # Update layout
        fig.update_layout(
            title=f"{strana_node} - {metric_name}",
            xaxis_title="Date",
            yaxis_title="Value",
            showlegend=True,
            template="plotly_white"
        )
        
        if output_file:
            fig.write_html(output_file)
            
        return fig
    
    def create_bar_plot(
        self,
        strana_node: str,
        metric_name: str,
        date: Optional[datetime] = None,
        output_file: Optional[str] = None
    ) -> go.Figure:
        """
        Create a bar plot for the specified stranaNode and metric using the latest date.
        
        Args:
            strana_node (str): The stranaNodeName to plot
            metric_name (str): The rmRiskMetricName to plot
            date (datetime, optional): Specific date to plot, defaults to latest
            output_file (str, optional): If provided, save the plot to this file
        
        Returns:
            go.Figure: Plotly figure object
        """
        # Filter data
        mask = (self.data['stranaNodeName'] == strana_node) & \
               (self.data['rmRiskMetricName'] == metric_name)
        plot_data = self.data[mask].copy()
        
        # Use latest date if not specified
        if date is None:
            date = plot_data['Date'].max()
        
        # Filter for specific date
        plot_data = plot_data[plot_data['Date'] == date]
        
        # Sort by maturity/currency if present
        def get_sort_key(metric_name):
            maturity = self._extract_maturity(metric_name)
            if maturity:
                # Convert to months for sorting
                unit = maturity[-1]
                value = int(maturity[:-1])
                if unit == 'Y':
                    return value * 12
                elif unit == 'M':
                    return value
                elif unit == 'W':
                    return value / 4
                elif unit == 'D':
                    return value / 30
            return float('inf')  # Put non-maturity items at the end
        
        plot_data = plot_data.sort_values(
            'consoMreMetricName',
            key=lambda x: x.map(lambda y: get_sort_key(str(y)))
        )
        
        # Create bar plot
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=plot_data['consoMreMetricName'],
            y=plot_data['consoValue'],
            text=plot_data['consoValue'].round(2),
            textposition='auto',
        ))
        
        # Update layout
        fig.update_layout(
            title=f"{strana_node} - {metric_name} ({date.strftime('%Y-%m-%d')})",
            xaxis_title="Metric",
            yaxis_title="Value",
            showlegend=False,
            template="plotly_white",
            xaxis_tickangle=-45
        )
        
        if output_file:
            fig.write_html(output_file)
            
        return fig

class VisualizationConfig:
    def __init__(self):
        """Initialize visualization configuration."""
        self.plot_types = {}  # {(strana_node, metric_name): ['bar', 'time_series']}
        
    def add_visualization(
        self,
        strana_node: str,
        metric_name: str,
        plot_types: List[str]
    ):
        """
        Add visualization configuration for a specific metric.
        
        Args:
            strana_node (str): The stranaNodeName
            metric_name (str): The rmRiskMetricName
            plot_types (List[str]): List of plot types ('bar' and/or 'time_series')
        """
        self.plot_types[(strana_node, metric_name)] = plot_types
        
    def get_plot_types(
        self,
        strana_node: str,
        metric_name: str
    ) -> List[str]:
        """Get configured plot types for a specific metric."""
        return self.plot_types.get((strana_node, metric_name), []) 