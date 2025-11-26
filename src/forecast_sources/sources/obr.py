"""Extract forecasts from OBR Economic and Fiscal Outlook."""

import pandas as pd
import requests
from pathlib import Path
from typing import Optional
import tempfile

# OBR detailed forecast table URLs (direct Excel file URLs)
OBR_URLS = {
    "november-2025": "https://obr.uk/docs/dlm_uploads/Economy_Detailed_forecast_tables_November_2025.xlsx",
    "march-2025": "https://obr.uk/docs/dlm_uploads/Economy_Detailed_forecast_tables_March_2025.xlsx",
}

# Mapping from metric names to (sheet_name, column_index)
# Column indices are 0-based, based on sheet 1.7 structure
METRIC_LOCATIONS = {
    # Sheet 1.7 - Inflation
    "rpi": ("1.7", 2),
    "cpi": ("1.7", 4),
    "cpih": ("1.7", 5),
    "mortgage_interest": ("1.7", 7),
    "rent": ("1.7", 8),
    # Sheet 1.6 - Labour market
    "average_earnings": ("1.6", None),  # Need to find column
    # Sheet 1.16 - Housing
    "house_prices": ("1.16", None),  # Need to find column
}


class OBRForecast:
    """Extract and access OBR Economic and Fiscal Outlook forecasts."""

    def __init__(self, edition: str, cache_dir: Optional[Path] = None):
        """
        Initialize OBR forecast extractor.

        Args:
            edition: Forecast edition (e.g., "november-2025", "march-2025")
            cache_dir: Directory to cache downloaded files
        """
        self.edition = edition
        self.cache_dir = (
            Path(cache_dir) if cache_dir else Path(tempfile.gettempdir())
        )
        self._data: dict[str, dict[int, float]] = {}
        self._load_data()

    def _get_excel_path(self) -> Path:
        """Download or retrieve cached Excel file."""
        cache_path = self.cache_dir / f"obr_{self.edition}_economy.xlsx"

        if not cache_path.exists():
            url = OBR_URLS.get(self.edition)
            if not url:
                raise ValueError(f"Unknown OBR edition: {self.edition}")

            response = requests.get(url, allow_redirects=True)
            response.raise_for_status()

            with open(cache_path, "wb") as f:
                f.write(response.content)

        return cache_path

    def _load_data(self):
        """Load all metrics from Excel file."""
        excel_path = self._get_excel_path()

        # Load sheet 1.7 for inflation metrics
        self._load_sheet_1_7(excel_path)
        # Load sheet 1.6 for earnings
        self._load_sheet_1_6(excel_path)
        # Load sheet 1.16 for house prices
        self._load_sheet_1_16(excel_path)

    def _load_sheet_1_7(self, excel_path: Path):
        """Load inflation metrics from sheet 1.7."""
        try:
            df = pd.read_excel(excel_path, sheet_name="1.7", header=None)
        except Exception as e:
            print(f"Warning: Could not load sheet 1.7: {e}")
            return

        # Column mapping for sheet 1.7
        col_map = {
            "rpi": 2,
            "cpi": 4,
            "cpih": 5,
            "mortgage_interest": 7,
            "rent": 8,
        }

        for metric, col in col_map.items():
            self._data[metric] = self._extract_annual_data(df, col)

    def _load_sheet_1_6(self, excel_path: Path):
        """Load labour market metrics from sheet 1.6."""
        try:
            df = pd.read_excel(excel_path, sheet_name="1.6", header=None)
        except Exception as e:
            print(f"Warning: Could not load sheet 1.6: {e}")
            return

        # Find the earnings growth column (header varies between editions)
        col = self._find_column_by_header(df, "Average weekly earnings growth")
        if col is None:
            col = self._find_column_by_header(df, "Average earnings growth")
        if col is not None:
            self._data["average_earnings"] = self._extract_annual_data(df, col)

    def _load_sheet_1_16(self, excel_path: Path):
        """Load housing metrics from sheet 1.16."""
        try:
            df = pd.read_excel(excel_path, sheet_name="1.16", header=None)
        except Exception as e:
            print(f"Warning: Could not load sheet 1.16: {e}")
            return

        # Find "House price index (per cent change" column
        col = self._find_column_by_header(df, "per cent change")
        if col is not None:
            self._data["house_prices"] = self._extract_annual_data(df, col)

    def _find_column_by_header(
        self, df: pd.DataFrame, header_text: str
    ) -> Optional[int]:
        """Find column index by searching for header text."""
        for row_idx in range(min(10, df.shape[0])):
            for col_idx in range(df.shape[1]):
                cell = df.iloc[row_idx, col_idx]
                if (
                    isinstance(cell, str)
                    and header_text.lower() in cell.lower()
                ):
                    return col_idx
        return None

    def _extract_annual_data(
        self, df: pd.DataFrame, col: int
    ) -> dict[int, float]:
        """
        Extract annual data from a column.

        The OBR tables have quarterly data followed by annual data.
        Annual rows have just a year (e.g., 2025) in column 1.
        """
        result = {}

        for row_idx in range(df.shape[0]):
            year_cell = df.iloc[row_idx, 1]
            # Check if this is an annual row (year between 2008 and 2035)
            if isinstance(year_cell, (int, float)) and pd.notna(year_cell):
                year = int(year_cell)
                if 2008 <= year <= 2035:
                    val = df.iloc[row_idx, col]
                    if pd.notna(val) and isinstance(val, (int, float)):
                        # Values are already in percentage form
                        result[year] = float(val)

        return result

    def get(self, metric: str, year: int) -> Optional[float]:
        """
        Get a forecast value.

        Args:
            metric: Metric name (e.g., "cpi", "rpi", "average_earnings")
            year: Forecast year

        Returns:
            Percentage value or None if not available
        """
        if metric not in self._data:
            return None
        return self._data[metric].get(year)

    def get_series(
        self, metric: str, years: Optional[list[int]] = None
    ) -> dict[int, Optional[float]]:
        """
        Get a series of forecast values.

        Args:
            metric: Metric name
            years: List of years (default: 2025-2030)

        Returns:
            Dict mapping year to value
        """
        if years is None:
            years = [2025, 2026, 2027, 2028, 2029, 2030]

        if metric not in self._data:
            return {y: None for y in years}

        return {y: self._data[metric].get(y) for y in years}

    def compare_to(
        self,
        other: "OBRForecast",
        metric: str,
        years: Optional[list[int]] = None,
    ) -> pd.DataFrame:
        """
        Compare this forecast to another.

        Args:
            other: Another OBRForecast to compare against
            metric: Metric to compare
            years: Years to include

        Returns:
            DataFrame with columns for each forecast
        """
        if years is None:
            years = [2025, 2026, 2027, 2028, 2029, 2030]

        data = {
            self.edition: [self.get(metric, y) for y in years],
            other.edition: [other.get(metric, y) for y in years],
        }

        return pd.DataFrame(data, index=years)

    @property
    def available_metrics(self) -> list[str]:
        """List of available metrics."""
        return list(self._data.keys())
