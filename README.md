# forecast-sources

Extract and compare economic forecasts from official sources (OBR, CBO, etc.).

## Installation

```bash
pip install -e .
```

## Usage

### Extract OBR forecasts

```python
from forecast_sources import OBRForecast

# Load November 2025 forecast
nov = OBRForecast("november-2025")

# Get a single value
cpi_2025 = nov.get("cpi", 2025)  # Returns 3.45

# Get a series
cpi_series = nov.get_series("cpi", years=[2025, 2026, 2027])

# Compare two forecasts
march = OBRForecast("march-2025")
comparison_df = nov.compare_to(march, metric="cpi")
```

### Generate comparison charts

```python
from forecast_sources.charts import generate_obr_comparison_chart

# Generate HTML chart comparing March and November 2025 forecasts
html = generate_obr_comparison_chart(
    base_edition="march-2025",
    comparison_edition="november-2025",
    output_path="docs/uk/obr-comparison.html"
)
```

## Available metrics

- `cpi` - Consumer Price Index inflation
- `rpi` - Retail Price Index inflation
- `cpih` - Consumer Price Index including Housing
- `average_earnings` - Average weekly earnings growth
- `mortgage_interest` - Mortgage interest payments growth
- `rent` - Rent growth
- `house_prices` - House price index growth

## Data sources

- [OBR Economic and Fiscal Outlook](https://obr.uk/efo/)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
```
