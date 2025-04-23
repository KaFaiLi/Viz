# Data Visualization Tool

A robust tool for visualizing financial data with support for different datasets and flexible visualization options.

## Features

- Supports loading data from CSV files
- Handles multiple types of metrics (maturity-based and currency-based)
- Automatic preprocessing of data
- Interactive visualization selection for each metric
- Two types of visualizations:
  - Bar plots (showing different maturities/currencies)
  - Time series plots (grouped by stranaNode)
- Grouped time series plots for better comparison
- Interactive plots using Plotly
- Output in HTML format for easy sharing and viewing

## Requirements

```bash
pip install -r requirements.txt
```

## Directory Structure

```
.
├── src/
│   ├── data_loader.py      # Handles data loading and preprocessing
│   └── data_visualizer.py  # Contains visualization logic
├── main.py                 # Main script to run the tool
├── requirements.txt        # Python dependencies
└── output/                 # Directory for output plots (created automatically)
```

## Input Data Format

The tool expects a CSV file with the following columns:

- `limId`: Limit ID
- `rmRiskIndicator`: Risk indicator
- `rmRiskMetricName`: Risk metric name
- `stranaNodeName`: Strana node name
- `consoValue`: Consolidated value
- `Date`: Date of the measurement
- `consoMreMetricName`: Consolidated MRE metric name
- `limMaxValue`: Maximum limit value (optional)
- `limMinValue`: Minimum limit value (optional)

## Usage

1. Place your CSV file in the project directory
2. Update the file path in `main.py` to point to your CSV file
3. Run the script:

```bash
python main.py
```

The script will:
1. Load and preprocess your data
2. Display available stranaNodes and their metrics
3. Ask for your visualization preferences for each metric:
   - `bar`: Create a bar plot
   - `time_series`: Include in grouped time series plot
   - `both`: Create both visualizations
   - `skip`: Skip this metric
4. Create and save the visualizations based on your choices

## Visualization Types

### Bar Plots
- Shows different maturities or currencies for a specific metric
- Uses the latest date in the dataset
- Automatically sorts by maturity period
- Displays values on each bar

### Time Series Plots
- Groups all time series plots for the same stranaNode together
- Shows limit lines (if available)
- Interactive legend to show/hide specific series
- Multiple metrics displayed as subplots for easy comparison

## Output

The tool generates interactive HTML plots in the `output` directory with the following naming convention:
- Bar plots: `{stranaNodeName}_{metricName}_bar.html`
- Grouped time series plots: `{stranaNodeName}_grouped_timeseries.html`

## Example Usage

```python
# Example of running the script and selecting visualizations
$ python main.py

Available stranaNodes: ['FICRATG10JGB', 'FICASIRATFLO']

For each stranaNode and metric, you can choose:
1. bar - Bar plot
2. time_series - Time series plot
3. both - Both bar and time series plots
4. skip - Skip this metric

Metrics for FICRATG10JGB:
Choose visualization type for CredBpv (bar/time_series/both/skip): both
Choose visualization type for CredBpv10Y (bar/time_series/both/skip): time_series
...
```

## Customization

You can customize the visualization configuration in `main.py` by modifying the `config.add_visualization()` calls. For example:

```python
# Configure specific plot types for a metric
config.add_visualization(
    strana_node='FICRATG10JGB',
    metric_name='CredBpv',
    plot_types=['bar']  # Only create bar plot for this metric
)
``` 