import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from typing import Dict, List, Optional, Union, Tuple, Set
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
    
    def _convert_maturity_to_months(self, maturity: str) -> float:
        """Convert maturity string to months for sorting."""
        if not maturity:
            return float('inf')
        
        value = int(maturity[:-1])
        unit = maturity[-1]
        
        if unit == 'Y':
            return value * 12
        elif unit == 'M':
            return value
        elif unit == 'W':
            return value / 4
        elif unit == 'D':
            return value / 30
        return float('inf')
    
    def get_available_strana_nodes(self) -> List[str]:
        """Return list of available stranaNodeName values."""
        return sorted(self.data['stranaNodeName'].unique())
    
    def get_mother_metrics(self, strana_node: str) -> List[str]:
        """
        Get list of mother metrics (metrics without maturity/currency specifications).
        
        Args:
            strana_node (str): The stranaNodeName to get metrics for
            
        Returns:
            List[str]: List of mother metrics
        """
        all_metrics = self.data[self.data['stranaNodeName'] == strana_node]['rmRiskMetricName'].unique()
        mother_metrics = []
        
        for metric in all_metrics:
            # If metric has no maturity and no currency, it's a mother metric
            if not self._extract_maturity(metric) and not self._extract_currency(metric):
                mother_metrics.append(metric)
        
        return sorted(mother_metrics)
    
    def get_all_related_metrics(self, strana_node: str, mother_metric: str) -> List[str]:
        """
        Get all metrics related to a mother metric, including sub-metrics with maturity/currency.
        Case-insensitive matching is used to find related metrics.
        
        Args:
            strana_node (str): The stranaNodeName
            mother_metric (str): The mother metric name
            
        Returns:
            List[str]: List of all related metrics, sorted by maturity/currency
        """
        # Get all metrics for this stranaNode
        all_metrics = self.data[self.data['stranaNodeName'] == strana_node]['rmRiskMetricName'].unique()
        
        # Find all metrics that contain the mother metric (case-insensitive)
        related_metrics = [m for m in all_metrics if mother_metric.lower() in m.lower()]
        
        # Sort metrics by maturity/currency
        def sort_key(metric):
            maturity = self._extract_maturity(metric)
            currency = self._extract_currency(metric)
            
            # Put exact matches (ignoring case) first
            if metric.lower() == mother_metric.lower():
                return (0, '')
            elif maturity:  # Then sort by maturity
                return (1, self._convert_maturity_to_months(maturity))
            elif currency:  # Then by currency
                return (2, currency)
            return (3, metric)  # Other cases
        
        return sorted(related_metrics, key=sort_key)
    
    def create_bar_plot(
        self,
        strana_node: str,
        mother_metric: str,
        date: Optional[datetime] = None,
        output_file: Optional[str] = None
    ) -> go.Figure:
        """
        Create a bar plot for all metrics related to the mother metric.
        
        Args:
            strana_node (str): The stranaNodeName to plot
            mother_metric (str): The mother metric name
            date (datetime, optional): Specific date to plot, defaults to latest
            output_file (str, optional): If provided, save the plot to this file
        """
        # Get all related metrics
        metrics = self.get_all_related_metrics(strana_node, mother_metric)
        
        # Filter data for all metrics
        mask = (self.data['stranaNodeName'] == strana_node) & \
               (self.data['rmRiskMetricName'].isin(metrics))
        plot_data = self.data[mask].copy()
        
        # Use latest date if not specified
        if date is None:
            date = plot_data['Date'].max()
        
        # Filter for specific date
        plot_data = plot_data[plot_data['Date'] == date]
        
        # Create bar plot
        fig = go.Figure()
        
        # Add bars
        fig.add_trace(go.Bar(
            x=metrics,  # Use pre-sorted metrics list
            y=plot_data.set_index('rmRiskMetricName').reindex(metrics)['consoValue'],
            text=plot_data.set_index('rmRiskMetricName').reindex(metrics)['consoValue'].round(2),
            textposition='auto',
        ))
        
        # Update layout
        fig.update_layout(
            title=f"{strana_node} - {mother_metric} and Related Metrics ({date.strftime('%Y-%m-%d')})",
            xaxis_title="Metric",
            yaxis_title="Value",
            showlegend=False,
            template="plotly_white",
            xaxis_tickangle=-45
        )
        
        if output_file:
            fig.write_html(output_file)
        
        return fig
    
    def create_time_series_plot(
        self,
        strana_node: str,
        mother_metric: str,
        output_file: Optional[str] = None
    ) -> go.Figure:
        """
        Create a time series plot with subplots for all metrics related to the mother metric.
        Each subplot will have independent axes and its own limit lines if available.
        Subplots are arranged in a 2-column grid layout.
        
        Args:
            strana_node (str): The stranaNodeName to plot
            mother_metric (str): The mother metric name
            output_file (str, optional): If provided, save the plot to this file
        """
        # Get all related metrics
        metrics = self.get_all_related_metrics(strana_node, mother_metric)
        
        # Filter data
        mask = (self.data['stranaNodeName'] == strana_node) & \
               (self.data['rmRiskMetricName'].isin(metrics))
        plot_data = self.data[mask].copy()
        
        # Calculate number of rows needed for 2 columns
        num_rows = (len(metrics) + 1) // 2  # Round up division
        
        # Create figure with subplots in 2 columns
        fig = make_subplots(
            rows=num_rows,
            cols=2,
            subplot_titles=[f"{metric}" for metric in metrics],
            vertical_spacing=0.2,  # Reduced spacing since we're using 2 columns
            horizontal_spacing=0.15,
            shared_xaxes=False     # Independent x-axes
        )
        
        # Calculate height based on number of rows (minimum 400px)
        height = max(250 * num_rows, 400)
        # Set width based on height to maintain good aspect ratio
        width = min(1200, height * 2)  # Cap width at 1200px
        
        # Add time series for each metric in separate subplots
        for idx, metric in enumerate(metrics, 1):
            # Calculate row and column (1-based indexing)
            row = (idx + 1) // 2
            col = 2 if idx % 2 == 0 else 1
            
            metric_data = plot_data[plot_data['rmRiskMetricName'] == metric].copy()
            metric_data = metric_data.sort_values('Date')
            
            # Add the time series
            fig.add_trace(
                go.Scatter(
                    x=metric_data['Date'],
                    y=metric_data['consoValue'],
                    name=metric,
                    mode='lines+markers',
                    showlegend=False
                ),
                row=row,
                col=col
            )
            
            # Add limit lines if they exist for this specific metric
            if not metric_data.empty:
                latest_data = metric_data.iloc[-1]
                
                if pd.notna(latest_data['limMaxValue']):
                    fig.add_hline(
                        y=latest_data['limMaxValue'],
                        line_dash="dash",
                        line_color="red",
                        annotation=dict(
                            text="Max Limit",
                            xanchor='left',
                            x=0,
                            yanchor='bottom'
                        ),
                        row=row,
                        col=col
                    )
                
                if pd.notna(latest_data['limMinValue']):
                    fig.add_hline(
                        y=latest_data['limMinValue'],
                        line_dash="dash",
                        line_color="red",
                        annotation=dict(
                            text="Min Limit",
                            xanchor='left',
                            x=0,
                            yanchor='top'
                        ),
                        row=row,
                        col=col
                    )
            
            # Add axis titles for each subplot
            fig.update_xaxes(title_text="Date", row=row, col=col)
            fig.update_yaxes(title_text="Value", row=row, col=col)
        
        # Update layout
        fig.update_layout(
            title=f"{strana_node} - {mother_metric} and Related Metrics Time Series",
            height=height,
            width=width,
            showlegend=False,
            template="plotly_white"
        )
        
        if output_file:
            fig.write_html(output_file)
        
        return fig

    def create_grouped_bar_plots(
        self,
        strana_node: str,
        mother_metrics: List[str],
        date: Optional[datetime] = None,
        output_file: Optional[str] = None
    ) -> go.Figure:
        """
        Create grouped bar plots for multiple mother metrics in the same stranaNode.
        Each mother metric and its related metrics will be in a separate subplot.
        Subplots are arranged in a 2-column grid layout.
        
        Args:
            strana_node (str): The stranaNodeName to plot
            mother_metrics (List[str]): List of mother metrics to plot
            date (datetime, optional): Specific date to plot, defaults to latest
            output_file (str, optional): If provided, save the plot to this file
        """
        # Calculate number of rows needed for 2 columns
        num_rows = (len(mother_metrics) + 1) // 2  # Round up division
        
        # Create figure with subplots in 2 columns
        fig = make_subplots(
            rows=num_rows,
            cols=2,
            subplot_titles=[f"{metric}" for metric in mother_metrics],
            vertical_spacing=0.2,
            horizontal_spacing=0.15
        )
        
        # Calculate height based on number of rows
        height = max(250 * num_rows, 400)
        # Set width based on height to maintain good aspect ratio
        width = min(1200, height * 2)  # Cap width at 1200px
        
        # Process each mother metric
        for idx, mother_metric in enumerate(mother_metrics, 1):
            # Calculate row and column (1-based indexing)
            row = (idx + 1) // 2
            col = 2 if idx % 2 == 0 else 1
            
            # Get all related metrics
            metrics = self.get_all_related_metrics(strana_node, mother_metric)
            
            # Filter data
            mask = (self.data['stranaNodeName'] == strana_node) & \
                   (self.data['rmRiskMetricName'].isin(metrics))
            plot_data = self.data[mask].copy()
            
            # Use latest date if not specified
            if date is None:
                date = plot_data['Date'].max()
            
            # Filter for specific date
            plot_data = plot_data[plot_data['Date'] == date]
            
            # Add bar plot
            fig.add_trace(
                go.Bar(
                    x=metrics,  # Use pre-sorted metrics list
                    y=plot_data.set_index('rmRiskMetricName').reindex(metrics)['consoValue'],
                    text=plot_data.set_index('rmRiskMetricName').reindex(metrics)['consoValue'].round(2),
                    textposition='auto',
                    name=mother_metric,
                    showlegend=False
                ),
                row=row,
                col=col
            )
            
            # Update axes
            fig.update_xaxes(title_text="Metric", row=row, col=col, tickangle=-45)
            fig.update_yaxes(title_text="Value", row=row, col=col)
        
        # Update layout
        fig.update_layout(
            title=f"{strana_node} - Bar Plots ({date.strftime('%Y-%m-%d')})",
            height=height,
            width=width,
            showlegend=False,
            template="plotly_white"
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