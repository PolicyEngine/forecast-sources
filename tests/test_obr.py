"""Tests for OBR forecast extraction.

These tests verify that extracted values match the official OBR
Economic and Fiscal Outlook detailed forecast tables.
"""

import pytest
from forecast_sources.sources.obr import OBRForecast


class TestOBRNovember2025:
    """Test November 2025 EFO values against official tables."""

    @pytest.fixture
    def forecast(self):
        return OBRForecast("november-2025")

    # CPI - Economy Table 1.7
    def test_cpi_2025(self, forecast):
        assert forecast.get("cpi", 2025) == pytest.approx(3.45, rel=0.01)

    def test_cpi_2026(self, forecast):
        assert forecast.get("cpi", 2026) == pytest.approx(2.48, rel=0.01)

    def test_cpi_2027(self, forecast):
        assert forecast.get("cpi", 2027) == pytest.approx(2.02, rel=0.01)

    def test_cpi_2028(self, forecast):
        assert forecast.get("cpi", 2028) == pytest.approx(2.04, rel=0.01)

    def test_cpi_2029(self, forecast):
        assert forecast.get("cpi", 2029) == pytest.approx(2.04, rel=0.01)

    def test_cpi_2030(self, forecast):
        assert forecast.get("cpi", 2030) == pytest.approx(2.00, rel=0.01)

    # RPI - Economy Table 1.7
    def test_rpi_2025(self, forecast):
        assert forecast.get("rpi", 2025) == pytest.approx(4.33, rel=0.01)

    def test_rpi_2026(self, forecast):
        assert forecast.get("rpi", 2026) == pytest.approx(3.71, rel=0.01)

    def test_rpi_2030(self, forecast):
        assert forecast.get("rpi", 2030) == pytest.approx(2.31, rel=0.01)

    # Average earnings - Economy Table 1.6
    def test_earnings_2025(self, forecast):
        assert forecast.get("average_earnings", 2025) == pytest.approx(
            5.17, rel=0.01
        )

    def test_earnings_2026(self, forecast):
        assert forecast.get("average_earnings", 2026) == pytest.approx(
            3.33, rel=0.01
        )

    # Mortgage interest - Economy Table 1.7
    def test_mortgage_interest_2025(self, forecast):
        assert forecast.get("mortgage_interest", 2025) == pytest.approx(
            10.98, rel=0.01
        )

    def test_mortgage_interest_2026(self, forecast):
        assert forecast.get("mortgage_interest", 2026) == pytest.approx(
            14.35, rel=0.01
        )

    def test_mortgage_interest_2027(self, forecast):
        assert forecast.get("mortgage_interest", 2027) == pytest.approx(
            10.32, rel=0.01
        )


class TestOBRMarch2025:
    """Test March 2025 EFO values against official tables."""

    @pytest.fixture
    def forecast(self):
        return OBRForecast("march-2025")

    # CPI - Economy Table 1.7
    def test_cpi_2025(self, forecast):
        assert forecast.get("cpi", 2025) == pytest.approx(3.21, rel=0.01)

    def test_cpi_2026(self, forecast):
        assert forecast.get("cpi", 2026) == pytest.approx(2.08, rel=0.01)

    # Average earnings - Economy Table 1.6
    def test_earnings_2025(self, forecast):
        assert forecast.get("average_earnings", 2025) == pytest.approx(
            4.32, rel=0.01
        )

    # Mortgage interest - Economy Table 1.7
    # Note: March values differ from previous policyengine-uk assumptions
    def test_mortgage_interest_2025(self, forecast):
        assert forecast.get("mortgage_interest", 2025) == pytest.approx(
            14.17, rel=0.01
        )

    def test_mortgage_interest_2026(self, forecast):
        assert forecast.get("mortgage_interest", 2026) == pytest.approx(
            13.25, rel=0.01
        )

    # March 2025 only goes to 2029 for most variables
    def test_mortgage_interest_2030_is_none(self, forecast):
        assert forecast.get("mortgage_interest", 2030) is None


class TestOBRForecastComparison:
    """Test comparing two forecasts."""

    def test_get_comparison_dataframe(self):
        march = OBRForecast("march-2025")
        november = OBRForecast("november-2025")

        df = november.compare_to(march, metric="cpi", years=[2025, 2026])

        assert len(df) == 2
        assert "march-2025" in df.columns
        assert "november-2025" in df.columns
        assert df.loc[2025, "november-2025"] == pytest.approx(3.45, rel=0.01)
        assert df.loc[2025, "march-2025"] == pytest.approx(3.21, rel=0.01)
