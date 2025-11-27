"""Generate comparison charts for economic forecasts."""

import plotly.graph_objects as go
from pathlib import Path
from typing import Optional

from .sources.obr import OBRForecast

# Metric metadata
METRICS = {
    "cpi": {
        "title": "CPI inflation (%)",
        "usage": (
            "<strong>Used in PolicyEngine to uprate:</strong> "
            '<span class="example">Universal Credit, PIP, Child Benefit, '
            "State Pension</span> "
            '<span class="count">and 44 other benefits and consumption '
            "variables</span>. Also used for absolute poverty thresholds, "
            "triple lock calculations, and real-terms analysis."
        ),
    },
    "rpi": {
        "title": "RPI inflation (%)",
        "usage": (
            "<strong>Used in PolicyEngine for:</strong> "
            '<span class="example">Private pension uprating</span> and '
            "fuel duty projections. RPI remains important for student loan "
            "interest rates and some legacy pension schemes."
        ),
    },
    "cpih": {
        "title": "CPIH inflation (%)",
        "usage": (
            "<strong>Used in PolicyEngine for:</strong> "
            '<span class="example">After-housing-costs (AHC) deflator'
            "</span> calculations. CPIH includes owner occupiers' housing "
            "costs, making it useful for real-terms comparisons that "
            "account for housing."
        ),
    },
    "average_earnings": {
        "title": "Average earnings growth (%)",
        "usage": (
            "<strong>Used in PolicyEngine to uprate:</strong> "
            '<span class="example">Employment income, pension contributions, '
            "student loan repayments</span> "
            '<span class="count">(6 variables)</span>. Also used in triple '
            "lock calculations for State Pension."
        ),
    },
    "mortgage_interest": {
        "title": "Mortgage interest growth (%)",
        "usage": (
            "<strong>Used in PolicyEngine to uprate:</strong> "
            '<span class="example">Mortgage interest repayments</span>. '
            "Affects housing cost projections for owner-occupiers with "
            "mortgages."
        ),
    },
    "rent": {
        "title": "Rent growth (%)",
        "usage": (
            "<strong>Used in PolicyEngine to uprate:</strong> "
            '<span class="example">Private rent</span> for households in '
            "the private rented sector."
        ),
    },
    "house_prices": {
        "title": "House price growth (%)",
        "usage": (
            "<strong>Used in PolicyEngine for:</strong> "
            "Stamp duty projections and property value calculations."
        ),
    },
    "social_rent": {
        "title": "Social rent growth (%)",
        "usage": (
            "<strong>Used in PolicyEngine to uprate:</strong> "
            '<span class="example">Social housing rent</span>. '
            "Derived from CPI + 1% with a one year lag, following the "
            "government's social rent policy."
        ),
    },
}


def generate_obr_comparison_chart(
    base_edition: str = "march-2025",
    comparison_edition: str = "november-2025",
    output_path: Optional[Path] = None,
    years: Optional[list[int]] = None,
) -> str:
    """
    Generate an interactive HTML chart comparing OBR forecasts.

    Args:
        base_edition: Earlier forecast edition (shown as dashed line)
        comparison_edition: Later forecast edition (shown as solid line)
        output_path: Path to write HTML file (optional)
        years: Years to include (default: 2025-2030)

    Returns:
        HTML string
    """
    if years is None:
        years = [2025, 2026, 2027, 2028, 2029, 2030]

    base = OBRForecast(base_edition)
    comparison = OBRForecast(comparison_edition)

    # Build data for all metrics
    data_js = "const data = {\n"
    for metric, meta in METRICS.items():
        base_values = [base.get(metric, y) for y in years]
        comp_values = [comparison.get(metric, y) for y in years]

        # Format values for JavaScript
        base_str = (
            "["
            + ", ".join(
                "null" if v is None else f"{v:.2f}" for v in base_values
            )
            + "]"
        )
        comp_str = (
            "["
            + ", ".join(
                "null" if v is None else f"{v:.2f}" for v in comp_values
            )
            + "]"
        )

        usage = meta["usage"].replace("'", "\\'")
        data_js += f"""    {metric}: {{
        {base_edition.replace('-', '_')}: {base_str},
        {comparison_edition.replace('-', '_')}: {comp_str},
        title: '{meta["title"]}',
        usage: '{usage}'
    }},
"""
    data_js += "};"

    # Calculate y-axis range
    all_values = []
    for metric in METRICS:
        all_values.extend(
            [v for v in [base.get(metric, y) for y in years] if v is not None]
        )
        all_values.extend(
            [
                v
                for v in [comparison.get(metric, y) for y in years]
                if v is not None
            ]
        )
    max_val = max(all_values) if all_values else 10
    y_max = ((max_val // 5) + 1) * 5 + 1  # Round up to nearest 5 + 1

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 10px;
            background: white;
        }}
        .controls {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
        }}
        .controls label {{
            font-size: 14px;
            font-weight: 500;
            color: #374151;
        }}
        .controls select {{
            padding: 8px 12px;
            border: 2px solid #319795;
            background: white;
            color: #374151;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
            font-weight: 500;
            min-width: 200px;
        }}
        .controls select:focus {{
            outline: none;
            border-color: #2C7A7B;
        }}
        #chart {{
            width: 100%;
            height: 350px;
        }}
        #usage {{
            margin-top: 10px;
            padding: 12px 16px;
            background: #F9FAFB;
            border-radius: 6px;
            font-size: 13px;
            color: #4B5563;
            line-height: 1.5;
        }}
        #usage strong {{
            color: #374151;
        }}
        #usage .example {{
            color: #319795;
            font-weight: 500;
        }}
        #usage .count {{
            color: #6B7280;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="controls">
        <label for="metric-select">Select metric:</label>
        <select id="metric-select" onchange="showChart(this.value)">
            <optgroup label="Inflation">
                <option value="cpi" selected>CPI inflation</option>
                <option value="rpi">RPI inflation</option>
                <option value="cpih">CPIH inflation</option>
            </optgroup>
            <optgroup label="Labour market">
                <option value="average_earnings">Average earnings</option>
            </optgroup>
            <optgroup label="Housing">
                <option value="house_prices">House prices</option>
                <option value="rent">Private rent</option>
                <option value="social_rent">Social rent</option>
                <option value="mortgage_interest">Mortgage interest</option>
            </optgroup>
        </select>
    </div>
    <div id="chart"></div>
    <div id="usage"></div>

    <script>
        const years = {years};
        const baseEdition = '{base_edition}';
        const compEdition = '{comparison_edition}';

        {data_js}

        function showChart(metric) {{
            const d = data[metric];

            // Filter out null values for base (which may have shorter series)
            const baseKey = baseEdition.replace(/-/g, '_');
            const compKey = compEdition.replace(/-/g, '_');

            const baseYears = [];
            const baseValues = [];
            for (let i = 0; i < years.length; i++) {{
                if (d[baseKey][i] !== null) {{
                    baseYears.push(years[i]);
                    baseValues.push(d[baseKey][i]);
                }}
            }}

            const trace1 = {{
                x: baseYears,
                y: baseValues,
                name: baseEdition.replace('-', ' ').replace(/\\b\\w/g, l => l.toUpperCase()),
                type: 'scatter',
                mode: 'lines+markers',
                line: {{ color: '#9CA3AF', width: 2, dash: 'dash' }},
                marker: {{ size: 8 }}
            }};

            const trace2 = {{
                x: years,
                y: d[compKey],
                name: compEdition.replace('-', ' ').replace(/\\b\\w/g, l => l.toUpperCase()),
                type: 'scatter',
                mode: 'lines+markers',
                line: {{ color: '#319795', width: 3 }},
                marker: {{ size: 10 }}
            }};

            const layout = {{
                title: {{
                    text: d.title,
                    font: {{
                        size: 18,
                        color: '#374151',
                        family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                    }}
                }},
                xaxis: {{
                    tickmode: 'array',
                    tickvals: years,
                    ticktext: years.map(String),
                    gridcolor: '#E5E7EB',
                    tickfont: {{
                        family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                        color: '#6B7280'
                    }}
                }},
                yaxis: {{
                    range: [0, {y_max}],
                    gridcolor: '#E5E7EB',
                    zeroline: true,
                    zerolinecolor: '#9CA3AF',
                    tickfont: {{
                        family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                        color: '#6B7280'
                    }},
                    ticksuffix: '%'
                }},
                legend: {{
                    orientation: 'h',
                    y: -0.2,
                    x: 0.5,
                    xanchor: 'center',
                    font: {{
                        family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                        color: '#374151'
                    }}
                }},
                margin: {{ t: 50, b: 100, l: 50, r: 30 }},
                plot_bgcolor: 'white',
                paper_bgcolor: 'white',
                hovermode: 'x unified',
                hoverlabel: {{
                    font: {{
                        family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                    }}
                }}
            }};

            const config = {{
                responsive: true,
                displayModeBar: false
            }};

            Plotly.newPlot('chart', [trace1, trace2], layout, config);

            // Update usage text
            document.getElementById('usage').innerHTML = d.usage;
        }}

        // Initial chart
        showChart('cpi');
    </script>
</body>
</html>
"""

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)

    return html


if __name__ == "__main__":
    # Generate chart to docs folder
    output = (
        Path(__file__).parent.parent.parent.parent
        / "docs"
        / "uk"
        / "obr-comparison.html"
    )
    generate_obr_comparison_chart(output_path=output)
    print(f"Generated chart at {output}")
