import httpx
from typing import Optional

from finsight.fetchers.base_fetcher import BaseFetcher


class NSEFetcher(BaseFetcher):
    """Best-effort fetcher for NSE India data.

    NSE actively blocks automated access. This fetcher uses session cookies
    and may fail. The system is designed to work without it.
    """

    BASE_URL = "https://www.nseindia.com"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._session_initialized = False

    def _init_session(self):
        """Initialize session by visiting NSE homepage to get cookies."""
        if self._session_initialized:
            return
        try:
            self._get(self.BASE_URL)
            self._session_initialized = True
        except Exception as e:
            self.logger.warning(f"Failed to initialize NSE session: {e}")

    def fetch_stock_quote(self, symbol: str) -> Optional[dict]:
        """Fetch stock quote from NSE API."""
        self._init_session()
        try:
            response = self._get(
                f"{self.BASE_URL}/api/quote-equity",
                params={"symbol": symbol.upper()},
            )
            data = response.json()
            price_info = data.get("priceInfo", {})
            info = data.get("info", {})
            return {
                "symbol": symbol.upper(),
                "name": info.get("companyName"),
                "cmp": price_info.get("lastPrice"),
                "open": price_info.get("open"),
                "high": price_info.get("intraDayHighLow", {}).get("max"),
                "low": price_info.get("intraDayHighLow", {}).get("min"),
                "prev_close": price_info.get("previousClose"),
                "change": price_info.get("change"),
                "change_pct": price_info.get("pChange"),
                "high_52w": price_info.get("weekHighLow", {}).get("max"),
                "low_52w": price_info.get("weekHighLow", {}).get("min"),
            }
        except Exception as e:
            self.logger.warning(f"NSE quote fetch failed for {symbol}: {e}")
            return None

    def fetch_fii_dii_data(self) -> Optional[dict]:
        """Fetch FII/DII activity data."""
        self._init_session()
        try:
            response = self._get(f"{self.BASE_URL}/api/fiidiiActivity")
            return response.json()
        except Exception as e:
            self.logger.warning(f"NSE FII/DII fetch failed: {e}")
            return None

    def fetch_index_data(self, index: str = "NIFTY 50") -> Optional[dict]:
        """Fetch index data from NSE."""
        self._init_session()
        try:
            response = self._get(f"{self.BASE_URL}/api/allIndices")
            data = response.json()
            for item in data.get("data", []):
                if item.get("index") == index:
                    return item
            return None
        except Exception as e:
            self.logger.warning(f"NSE index fetch failed: {e}")
            return None
