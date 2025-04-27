# Financial Risk Metrics Visualization Tool

A comprehensive visualization tool for financial risk metrics data, supporting multiple visualization types and automated dashboard generation.

## Features

### Data Handling
- Flexible CSV data loading and preprocessing
- Support for various metric types:
  - Maturity-based metrics (e.g., 3M, 1Y, 2Y)
  - Currency-based metrics (e.g., [USD], [EUR], [JPY])
  - Basis point value (BPV) metrics
  - Value at Risk (VaR) metrics
- Automatic metric categorization and sorting

### Visualization Types
- **Bar Plots**:
  - Single metric visualization with related sub-metrics
  - Dynamic height adjustment based on metric count
  - Automatic sorting by maturity/currency
  - Value labels on bars
  - Minimum height of 600px for readability
  
- **Grouped Bar Plots**:
  - Multiple metrics in a 2-column grid layout
  - Dynamic subplot sizing and spacing
  - Automatic margin adjustment for readability
  - Height scales with number of metrics (400px per row + margins)

- **Time Series Plots**:
  - Interactive line plots with markers
  - Support for limit lines (max/min values)
  - Multiple metrics as subplots
  - Independent axes for better data visibility
  - Customizable annotations and legends

### Dashboard Generation
- Automated HTML dashboard creation
- Responsive grid layout for metric cards
- Interactive metric cards with hover effects
- Categorized by stranaNode
- Modern UI with consistent styling
- Mobile-responsive design

## Requirements

```bash
pip install -r requirements.txt
```

Required packages:
- pandas
- plotly
- numpy
- logging

## Project Structure

```
.
├── src/
│   ├── data_visualizer.py    # Core visualization logic
│   ├── html_generator.py     # Dashboard HTML generation
│   ├── special_metrics_rules.py  # Custom metric handling rules
│   └── config.py            # Visualization configuration
├── Input/
│   ├── gen.py              # Sample data generator
│   └── fake_data.csv       # Generated sample data
├── main.py                 # Main execution script
├── requirements.txt        # Python dependencies
└── output/                # Generated visualizations (created automatically)
    └── {stranaNode}/      # Organized by stranaNode
```

## Input Data Format

The tool expects a CSV file with the following columns:

| Column Name | Description | Type |
|------------|-------------|------|
| limId | Limit identifier | Integer |
| rmRiskIndicator | Risk indicator type | String |
| rmRiskMetricName | Risk metric name | String |
| stranaNodeName | Strana node identifier | String |
| consoValue | Consolidated value | Float |
| Date | Measurement date | Date (MM/DD/YYYY) |
| consoMreMetricName | Consolidated MRE metric name | String |
| limMaxValue | Maximum limit value | Float (optional) |
| limMinValue | Minimum limit value | Float (optional) |

## Usage

1. **Basic Usage**:
   ```bash
   python main.py
   ```

2. **Configuration**:
   - Edit `src/config.py` to customize visualization settings
   - Example configuration:
   ```python
   {
       'FICRATG10JGB': {
           'metrics_config': [
               {
                   'mother_metrics': ['CredBpv', 'FX', 'FXUSD'],
                   'plot_types': ['bar', 'time_series']
               }
           ]
       }
   }
   ```

3. **Custom Metric Rules**:
   - Add patterns to `special_metrics_rules.py` for custom metric handling
   - Supports include/exclude patterns for metric filtering

## Output Structure

```
output/
├── {stranaNode1}/
│   ├── {metric}_bar.html           # Bar plot visualizations
│   ├── {metric}_timeseries.html    # Time series visualizations
│   └── grouped_bar_plots.html      # Combined bar plots
├── {stranaNode2}/
│   └── ...
└── dashboard.html                  # Main dashboard page
```

## Visualization Details

### Bar Plot Features
- Dynamic height calculation: `max(600px, 100px * metrics_count)`
- Maximum width: 1200px
- Automatic x-axis label rotation (-45°)
- Value labels on bars
- Increased margins for label visibility

### Grouped Bar Plot Features
- Two-column layout
- Height per row: 400px + margins
- Minimum height: 600px
- Dynamic vertical spacing
- Automatic x-axis label rotation (-90°)

### Time Series Plot Features
- Interactive zoom and pan
- Hover tooltips with values
- Limit line indicators
- Independent y-axes
- Customizable subplot layout

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 