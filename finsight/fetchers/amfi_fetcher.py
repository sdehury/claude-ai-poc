import pandas as pd
from datetime import datetime
from typing import Optional

from finsight.fetchers.base_fetcher import BaseFetcher
from finsight.models.mutual_fund import MutualFundScheme


class AMFIFetcher(BaseFetcher):
    """Fetcher for mutual fund data via the free AMFI/mfapi.in API."""

    BASE_URL = "https://api.mfapi.in/mf"

    def search_schemes(self, query: str) -> list[MutualFundScheme]:
        """Search for mutual fund schemes by name."""
        data = self._get_json(f"{self.BASE_URL}/search?q={query}")
        return [
            MutualFundScheme(
                scheme_code=str(item["schemeCode"]),
                scheme_name=item["schemeName"],
            )
            for item in data
        ]

    def fetch_nav_history(self, scheme_code: str) -> tuple[pd.DataFrame, dict]:
        """Fetch complete NAV history for a mutual fund scheme.

        Returns:
            (nav_dataframe, meta_dict)
            - nav_dataframe: DataFrame with DatetimeIndex and 'nav' column (float)
            - meta_dict: scheme metadata (fund_house, scheme_name, etc.)
        """
        data = self._get_json(f"{self.BASE_URL}/{scheme_code}")

        meta = data.get("meta", {})
        nav_data = data.get("data", [])

        if not nav_data:
            raise ValueError(f"No NAV data for scheme {scheme_code}")

        records = []
        for entry in nav_data:
            try:
                date = datetime.strptime(entry["date"], "%d-%m-%Y")
                nav = float(entry["nav"])
                records.append({"date": date, "nav": nav})
            except (ValueError, KeyError):
                continue

        df = pd.DataFrame(records)
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)

        return df, meta

    def fetch_scheme_details(self, scheme_code: str) -> MutualFundScheme:
        """Fetch current details for a specific scheme."""
        data = self._get_json(f"{self.BASE_URL}/{scheme_code}")
        meta = data.get("meta", {})
        nav_data = data.get("data", [])

        latest_nav = None
        latest_date = None
        if nav_data:
            latest_nav = float(nav_data[0]["nav"])
            latest_date = nav_data[0]["date"]

        return MutualFundScheme(
            scheme_code=str(scheme_code),
            scheme_name=meta.get("scheme_name", "Unknown"),
            amc=meta.get("fund_house"),
            category=meta.get("scheme_category"),
            nav=latest_nav,
            nav_date=latest_date,
        )

    def fetch_all_schemes(self) -> list[dict]:
        """Fetch list of all available mutual fund schemes."""
        return self._get_json(self.BASE_URL)
