import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from typing import Dict, List, Optional, Union, Tuple, Set
from datetime import datetime
# Import the rules
from src.special_metrics_rules import special_metric_rules
import logging

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
        Applies filtering rules from special_metric_rules if defined.
        
        Args:
            strana_node (str): The stranaNodeName
            mother_metric (str): The mother metric name
            
        Returns:
            List[str]: List of all related metrics, sorted by maturity/currency
        """
        # Get all metrics for this stranaNode
        all_metrics = self.data[self.data['stranaNodeName'] == strana_node]['rmRiskMetricName'].unique()
        
        related_metrics: List[str] = []

        if mother_metric in special_metric_rules:
            rules = special_metric_rules[mother_metric]
            include_pattern = rules.get("include_pattern")
            exclude_pattern = rules.get("exclude_pattern")

            if include_pattern:
                # If include_pattern is specified, it defines the set directly from all_metrics.
                # This allows patterns to include metrics that don't necessarily contain the mother_metric string itself (e.g., STTHH for VaR).
                related_metrics = [m for m in all_metrics if re.search(include_pattern, m, re.IGNORECASE)]
                
                # Then, apply exclude_pattern to this specifically selected set
                if exclude_pattern:
                    related_metrics = [m for m in related_metrics if not re.search(exclude_pattern, m, re.IGNORECASE)]
            else:
                # No include_pattern, but other rules (like exclude_pattern only) might exist.
                # Default to finding metrics that contain the mother_metric string (case-insensitive).
                related_metrics = [m for m in all_metrics if mother_metric.lower() in m.lower()]
                if exclude_pattern: # Apply exclude_pattern if it exists without an include_pattern
                    related_metrics = [m for m in related_metrics if not re.search(exclude_pattern, m, re.IGNORECASE)]
        else:
            # No special rules at all for this mother_metric.
            # Default to finding metrics that contain the mother_metric string (case-insensitive).
            related_metrics = [m for m in all_metrics if mother_metric.lower() in m.lower()]

        # Sort metrics by maturity/currency
        def sort_key(metric):
            maturity = self._extract_maturity(metric)
            currency = self._extract_currency(metric)
            
            # Put exact matches (ignoring case) of the mother_metric first
            if metric.lower() == mother_metric.lower():
                return (0, '')
            elif maturity:  # Then sort by maturity
                return (1, self._convert_maturity_to_months(maturity))
            elif currency:  # Then by currency
                return (2, currency)
            return (3, metric)  # Other cases (alphabetical for metrics without specific components or after primary sorting)
        
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
               (self.data['consoMreMetricName'].isin(metrics))
        plot_data = self.data[mask].copy()
        
        # Use latest date if not specified
        if date is None:
            date = plot_data['consoValueDate'].max()
        
        # Filter for specific date
        plot_data = plot_data[plot_data['consoValueDate'] == date]
        
        # Create bar plot
        fig = go.Figure()
        
        # Add bars
        fig.add_trace(go.Bar(
            x=metrics,  # Use pre-sorted metrics list
            y=plot_data.set_index('consoMreMetricName').reindex(metrics)['consoValue'],
            text=plot_data.set_index('consoMreMetricName').reindex(metrics)['consoValue'].round(2),
            textposition='auto',
        ))
        
        # Fixed height and width
        fixed_height = 1000
        fixed_width = 1800
        
        # Update layout
        fig.update_layout(
            title=f"{strana_node} - {mother_metric} and Related Metrics ({date.strftime('%Y-%m-%d')})",
            xaxis_title="Metric",
            yaxis_title="Value",
            showlegend=False,
            template="plotly_white",
            xaxis_tickangle=-45, # Rotated labels to prevent overlap
            height=fixed_height,
            width=fixed_width,
            margin=dict(t=100, b=150, l=70, r=70),  # Adjusted margins, esp. bottom for rotated labels
            xaxis_automargin=True, # Allow x-axis to use more margin if needed for labels
            yaxis_automargin=True
        )
        
        if output_file:
            fig.write_html(output_file)
        
        return fig

    def _prepare_time_series_layout_config(self, num_metrics: int) -> dict:
        """
        Calculate layout configuration for time series plots.

        Args:
            num_metrics (int): Number of metrics to be plotted.

        Returns:
            dict: Configuration for num_rows, vertical_spacing, height, and width.
        """
        fixed_height = 1000
        fixed_width = 1800

        if num_metrics == 0:
            return {'num_rows': 1, 'vertical_spacing': 0.2, 'height': fixed_height, 'width': fixed_width}

        num_rows = (num_metrics + 1) // 2
        # Adjust vertical spacing: if num_rows is 1, spacing is not applicable between subplots.
        # If num_rows > 1, calculate spacing. Ensure it's not too small.
        # Max spacing can be 0.5 (50% of subplot height), min 0.05 (5%).
        # Total height for subplots themselves (excluding spacing) must be positive.
        # Let V be vertical_spacing (as a fraction of subplot height).
        # Total height = num_rows * subplot_height + (num_rows - 1) * V * subplot_height
        # For simplicity here, plotly's vertical_spacing is a fraction of the total available height for subplots.
        # We'll keep the existing logic but ensure it adapts to the fixed height.
        # The actual height of each subplot will shrink if num_rows is large.
        vertical_spacing = min(0.2, 0.8 / (num_rows - 1) if num_rows > 1 else 0.2)
        if num_rows > 1 and fixed_height / num_rows < 100: # If subplots get too small, reduce spacing
             vertical_spacing = max(0.05, 0.4 / (num_rows -1))


        return {'num_rows': num_rows, 'vertical_spacing': vertical_spacing, 'height': fixed_height, 'width': fixed_width}

    def _add_time_series_subplot_elements(
        self,
        fig: go.Figure,
        metric_data: pd.DataFrame,
        metric_name: str,
        row: int,
        col: int,
        event_dates: Optional[List[datetime]]
    ):
        """
        Add traces, limit lines, event lines, and configure axes for a single subplot.
        Assumes metric_data is already sorted by 'consoValueDate'.
        """
        # Add the time series trace
        fig.add_trace(
            go.Scatter(
                x=metric_data['consoValueDate'],
                y=metric_data['consoValue'],
                name=metric_name, # Used for hover text, legend is off
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
                    annotation=dict(text="Max Limit", xanchor='left', x=0, yanchor='bottom'),
                    row=row,
                    col=col
                )
            if pd.notna(latest_data['limMinValue']):
                fig.add_hline(
                    y=latest_data['limMinValue'],
                    line_dash="dash",
                    line_color="red",
                    annotation=dict(text="Min Limit", xanchor='left', x=0, yanchor='top'),
                    row=row,
                    col=col
                )

        # Add event date lines if specified
        if event_dates:
            for event_date in event_dates:
                if isinstance(event_date, datetime): # Ensure it's a datetime object
                    fig.add_vline(
                        x=event_date.timestamp() * 1000, # Convert datetime to milliseconds
                        line_width=1,
                        line_dash="dot",
                        line_color="darkgrey",
                        row=row,
                        col=col
                    )
        
        # Configure axes for this subplot
        fig.update_xaxes(title_text="", row=row, col=col)
        fig.update_yaxes(title_text="Value", row=row, col=col)

    def _generate_subplot_title_annotation(
        self,
        fig: go.Figure, # Needed for get_subplot domain
        metric_name: str,
        row: int,
        col: int,
        has_data: bool
    ) -> dict:
        """
        Generate the annotation dictionary for a subplot title.
        """
        x_domain, y_domain = fig.get_subplot(row=row, col=col).xaxis.domain, fig.get_subplot(row=row, col=col).yaxis.domain
        x_pos = (x_domain[0] + x_domain[1]) / 2
        y_pos = y_domain[1] + 0.02 # Adjust offset as needed

        title_text = f"<b>{metric_name}</b>"
        if not has_data:
            title_text += " (No Data)"

        return dict(
            text=title_text,
            xref="paper", yref="paper",
            x=x_pos, y=y_pos,
            xanchor='center', yanchor='bottom',
            showarrow=False,
            font=dict(size=14) # Adjust size as needed
        )

    def create_time_series_plot(
        self,
        strana_node: str,
        mother_metric: str,
        output_file: Optional[str] = None,
        event_dates: Optional[List[datetime]] = None  # New parameter for event dates
    ) -> go.Figure:
        """
        Create a time series plot with subplots for all metrics related to the mother metric.
        Each subplot will have independent axes and its own limit lines if available.
        Subplots are arranged in a 2-column grid layout.
        Vertical lines can be added for specified event dates.
        
        Args:
            strana_node (str): The stranaNodeName to plot
            mother_metric (str): The mother metric name
            output_file (str, optional): If provided, save the plot to this file
            event_dates (Optional[List[datetime]], optional): A list of dates to mark with vertical lines.
        """
        # Get all related metrics
        metrics = self.get_all_related_metrics(strana_node, mother_metric)

        if not metrics:
            logging.warning(f"No metrics found for mother_metric '{mother_metric}' in stranaNode '{strana_node}'. Skipping time series plot generation.")
            fig = go.Figure()
            fig.update_layout(
                title=f"{strana_node} - {mother_metric} - No Metrics Found",
                height=1000, # Fixed height
                width=1800  # Fixed width
            )
            if output_file:
                fig.write_html(output_file)
            return fig
        
        # Filter data ONCE for all relevant metrics and sort by date.
        mask = (self.data['stranaNodeName'] == strana_node) & \
               (self.data['consoMreMetricName'].isin(metrics))
        # .copy() ensures we operate on a distinct DataFrame for this plot.
        relevant_plot_data = self.data[mask].copy()
        relevant_plot_data.sort_values('consoValueDate', inplace=True)

        # Calculate layout parameters using fixed height and width
        layout_config = self._prepare_time_series_layout_config(len(metrics))
        
        # Create figure with subplots
        fig = make_subplots(
            rows=layout_config['num_rows'],
            cols=2, # Fixed at 2 columns
            vertical_spacing=layout_config['vertical_spacing'],
            horizontal_spacing=0.1, # Reduced horizontal spacing slightly
            shared_xaxes=False     # Independent x-axes
        )
        
        subplot_title_annotations = [] # Initialize list for annotations

        # Add time series for each metric in separate subplots
        for idx, current_metric_name in enumerate(metrics, 1):
            # Calculate row and column (1-based indexing)
            row = (idx + 1) // 2
            col = 2 if idx % 2 == 0 else 1
            
            metric_data_subset = relevant_plot_data[relevant_plot_data['consoMreMetricName'] == current_metric_name]
            
            has_data = not metric_data_subset.empty

            self._add_time_series_subplot_elements(
                fig, metric_data_subset, current_metric_name, row, col, event_dates
            )
            
            annotation = self._generate_subplot_title_annotation(
                fig, current_metric_name, row, col, has_data
            )
            subplot_title_annotations.append(annotation)
        
        # Update overall figure layout
        fig.update_layout(
            title=f"{strana_node} - {mother_metric} and Related Metrics Time Series",
            height=layout_config['height'], # This will be 1000
            width=layout_config['width'],   # This will be 1800
            showlegend=False,
            template="plotly_white",
            annotations=subplot_title_annotations,
            margin=dict(t=100, b=70, l=70, r=70) # Adjusted margins
        )
        
        # Ensure axes within subplots use automargin for labels
        for i in range(1, layout_config['num_rows'] + 1):
            for j in range(1, 3): # 2 columns
                fig.update_xaxes(row=i, col=j, automargin=True)
                fig.update_yaxes(row=i, col=j, automargin=True)

        if output_file:
            fig.write_html(output_file)
        
        return fig

    def create_grouped_bar_plots(
        self,
        strana_node: str,
        mother_metrics: List[str],
        selected_dates: Optional[Union[datetime, List[datetime]]] = None,
        output_file: Optional[str] = None
    ) -> go.Figure:
        """
        Create grouped bar plots for multiple mother metrics in the same stranaNode.
        Each mother metric and its related metrics will be in a separate subplot.
        If selected_dates are provided, data for these dates will be plotted.
        If multiple dates are selected, bars will be grouped by date for comparison.
        If selected_dates is None, the latest available date for each subplot's metrics is used.
        
        Args:
            strana_node (str): The stranaNodeName to plot
            mother_metrics (List[str]): List of mother metrics to plot
            selected_dates (Optional[Union[datetime, List[datetime]]], optional): 
                Specific date or list of dates to plot. Defaults to None (latest for each subplot).
            output_file (str, optional): If provided, save the plot to this file
        """
        fixed_height = 1000
        fixed_width = 1800

        # Calculate number of rows needed for 2 columns
        num_rows = (len(mother_metrics) + 1) // 2 if mother_metrics else 1
        
        # Adjust vertical spacing, similar to _prepare_time_series_layout_config
        vertical_spacing = min(0.2, 0.8 / (num_rows - 1) if num_rows > 1 else 0.2)
        if num_rows > 1 and fixed_height / num_rows < 150: # If subplots get too small, reduce spacing
             vertical_spacing = max(0.05, 0.4 / (num_rows -1))
        horizontal_spacing = 0.1 # Reduced horizontal spacing

        dates_provided_by_user = False
        dates_for_plot_generation: List[datetime] = []

        if isinstance(selected_dates, datetime):
            dates_for_plot_generation = [selected_dates]
            dates_provided_by_user = True
        elif isinstance(selected_dates, list):
            if all(isinstance(d, datetime) for d in selected_dates):
                if selected_dates:
                    dates_for_plot_generation = sorted(list(set(selected_dates)))
                    dates_provided_by_user = True
                else:
                    logging.warning(f"Empty list of dates provided for {strana_node}. Generating empty plot.")
                    fig = go.Figure()
                    fig.update_layout(title=f"{strana_node} - No dates specified for plotting", height=fixed_height, width=fixed_width)
                    if output_file:
                        fig.write_html(output_file)
                    return fig
            else:
                logging.error(f"Invalid list contents for selected_dates in create_grouped_bar_plots for {strana_node}. Expected list of datetimes. Generating empty plot.")
                fig = go.Figure()
                fig.update_layout(title=f"{strana_node} - Error: Invalid date input format", height=fixed_height, width=fixed_width)
                if output_file:
                    fig.write_html(output_file)
                return fig
        elif selected_dates is not None:
            logging.error(f"Invalid type for selected_dates in create_grouped_bar_plots for {strana_node}. Expected datetime, list of datetimes, or None. Generating empty plot.")
            fig = go.Figure()
            fig.update_layout(title=f"{strana_node} - Error: Invalid date input type", height=fixed_height, width=fixed_width)
            if output_file:
                fig.write_html(output_file)
            return fig
        
        if not mother_metrics:
            logging.warning(f"No mother metrics provided for {strana_node}. Generating empty plot.")
            fig = go.Figure()
            fig.update_layout(title=f"{strana_node} - No Mother Metrics Specified", height=fixed_height, width=fixed_width)
            if output_file:
                fig.write_html(output_file)
            return fig

        fig = make_subplots(
            rows=num_rows,
            cols=2,
            subplot_titles=[f"{metric}" for metric in mother_metrics],
            vertical_spacing=vertical_spacing,
            horizontal_spacing=horizontal_spacing
        )
        
        traces_added = False
        dates_already_in_legend = set()

        for idx, mother_metric in enumerate(mother_metrics, 1):
            row = (idx + 1) // 2
            col = 2 if idx % 2 == 0 else 1
            
            metrics = self.get_all_related_metrics(strana_node, mother_metric)
            
            current_mother_metric_data = self.data[
                (self.data['stranaNodeName'] == strana_node) &
                (self.data['consoMreMetricName'].isin(metrics))
            ]

            if current_mother_metric_data.empty:
                logging.info(f"No data available for mother metric {mother_metric} in {strana_node} before date filtering.")
                # Update subplot title to indicate no data
                fig.layout.annotations[idx-1].text = f"{mother_metric}<br>(No Data)"
                continue

            actual_dates_this_subplot: List[datetime] = []
            data_for_bars_this_subplot: pd.DataFrame

            if dates_provided_by_user:
                actual_dates_this_subplot = dates_for_plot_generation
                data_for_bars_this_subplot = current_mother_metric_data[current_mother_metric_data['consoValueDate'].isin(actual_dates_this_subplot)]
            else: 
                latest_date_for_subplot = current_mother_metric_data['consoValueDate'].max()
                if pd.isna(latest_date_for_subplot): # Handle case where no dates exist after filtering
                    logging.info(f"No valid latest date for mother metric {mother_metric} in {strana_node}.")
                    fig.layout.annotations[idx-1].text = f"{mother_metric}<br>(No Data)"
                    continue
                actual_dates_this_subplot = [latest_date_for_subplot]
                data_for_bars_this_subplot = current_mother_metric_data[current_mother_metric_data['consoValueDate'] == latest_date_for_subplot]

            if not actual_dates_this_subplot or data_for_bars_this_subplot.empty:
                logging.info(f"No data for subplot {mother_metric} for determined dates: {actual_dates_this_subplot}")
                fig.layout.annotations[idx-1].text = f"{mother_metric}<br>(No Data for Selected Dates)"
                continue
            
            actual_dates_this_subplot.sort() 

            for plot_date in actual_dates_this_subplot:
                date_specific_data = data_for_bars_this_subplot[data_for_bars_this_subplot['consoValueDate'] == plot_date]
                
                if date_specific_data.empty:
                    continue

                y_values = []
                text_values = []
                value_map = date_specific_data.set_index('consoMreMetricName')['consoValue']
                
                for m_name in metrics:
                    value = value_map.get(m_name, None)
                    y_values.append(value)
                    text_values.append(f"{value:.2f}" if pd.notna(value) else "")

                current_date_str = plot_date.strftime('%Y-%m-%d')
                is_first_occurrence_for_legend = current_date_str not in dates_already_in_legend

                fig.add_trace(
                    go.Bar(
                        x=metrics,
                        y=y_values,
                        text=text_values,
                        textposition='auto',
                        name=current_date_str, 
                        legendgroup=current_date_str, 
                        showlegend=dates_provided_by_user and is_first_occurrence_for_legend
                    ),
                    row=row,
                    col=col
                )
                traces_added = True
                if dates_provided_by_user and is_first_occurrence_for_legend:
                    dates_already_in_legend.add(current_date_str)
            
            fig.update_xaxes(title_text=None, row=row, col=col, tickangle=-90, automargin=True)
            fig.update_yaxes(title_text="Value", row=row, col=col, automargin=True)
        
        title_date_str = "Latest Available Data"
        if dates_provided_by_user:
            if dates_for_plot_generation:
                title_date_str_parts = [d.strftime('%Y-%m-%d') for d in dates_for_plot_generation]
                title_date_str = ", ".join(title_date_str_parts)
                if len(title_date_str) > 40: 
                    title_date_str = f"{len(title_date_str_parts)} Selected Dates"
            else: 
                 title_date_str = "No Dates Specified"
        elif not traces_added:
            title_date_str = "No Data Available"
            
        fig.update_layout(
            title=f"{strana_node} - Grouped Bar Plots ({title_date_str})",
            height=fixed_height,
            width=fixed_width,
            barmode='group',
            showlegend=dates_provided_by_user and len(dates_already_in_legend) > 0, # Show legend only if dates were given and at least one was plotted
            template="plotly_white",
            margin=dict(t=100, b=100, l=70, r=70) # Adjusted margins
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
            metric_name (str): The consoMreMetricName
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