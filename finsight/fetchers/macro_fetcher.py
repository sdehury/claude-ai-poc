from typing import Optional
from finsight.fetchers.base_fetcher import BaseFetcher


class MacroFetcher(BaseFetcher):
    """Fetcher for macroeconomic data from World Bank and FRED APIs."""

    WORLDBANK_URL = "https://api.worldbank.org/v2"

    def fetch_india_gdp_growth(self, years: int = 5) -> Optional[list[dict]]:
        """Fetch India GDP growth rate (annual %)."""
        return self._fetch_worldbank_indicator(
            "IN", "NY.GDP.MKTP.KD.ZG", years
        )

    def fetch_india_inflation(self, years: int = 5) -> Optional[list[dict]]:
        """Fetch India CPI inflation (annual %)."""
        return self._fetch_worldbank_indicator(
            "IN", "FP.CPI.TOTL.ZG", years
        )

    def fetch_us_gdp_growth(self, years: int = 5) -> Optional[list[dict]]:
        """Fetch US GDP growth rate."""
        return self._fetch_worldbank_indicator(
            "US", "NY.GDP.MKTP.KD.ZG", years
        )

    def fetch_global_indicators(self) -> dict:
        """Fetch key global macro indicators."""
        indicators = {}

        india_gdp = self.fetch_india_gdp_growth(3)
        if india_gdp:
            latest = next((r for r in india_gdp if r["value"] is not None), None)
            if latest:
                indicators["india_gdp_growth"] = latest["value"]
                indicators["india_gdp_year"] = latest["year"]

        india_cpi = self.fetch_india_inflation(3)
        if india_cpi:
            latest = next((r for r in india_cpi if r["value"] is not None), None)
            if latest:
                indicators["india_inflation"] = latest["value"]
                indicators["india_inflation_year"] = latest["year"]

        us_gdp = self.fetch_us_gdp_growth(3)
        if us_gdp:
            latest = next((r for r in us_gdp if r["value"] is not None), None)
            if latest:
                indicators["us_gdp_growth"] = latest["value"]
                indicators["us_gdp_year"] = latest["year"]

        return indicators

    def _fetch_worldbank_indicator(
        self, country: str, indicator: str, years: int
    ) -> Optional[list[dict]]:
        """Fetch a World Bank indicator for a country."""
        try:
            url = (
                f"{self.WORLDBANK_URL}/country/{country}"
                f"/indicator/{indicator}"
            )
            data = self._get_json(
                url,
                params={
                    "format": "json",
                    "per_page": years,
                    "mrv": years,
                },
            )

            if not isinstance(data, list) or len(data) < 2:
                return None

            records = []
            for entry in data[1]:
                records.append({
                    "year": entry.get("date"),
                    "value": entry.get("value"),
                    "indicator": entry.get("indicator", {}).get("value"),
                })
            return records
        except Exception as e:
            self.logger.warning(f"World Bank fetch failed ({indicator}): {e}")
            return None
