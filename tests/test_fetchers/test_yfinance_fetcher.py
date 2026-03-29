import pytest
from finsight.fetchers.yfinance_fetcher import YFinanceFetcher


@pytest.mark.integration
class TestYFinanceFetcher:
    """Integration tests that hit real Yahoo Finance API."""

    def setup_method(self):
        self.fetcher = YFinanceFetcher()

    def test_fetch_quote_reliance(self):
        quote = self.fetcher.fetch_quote("RELIANCE")
        assert quote.symbol == "RELIANCE"
        assert quote.cmp > 0
        assert quote.high_52w is not None
        assert quote.low_52w is not None
        assert quote.high_52w >= quote.low_52w

    def test_fetch_history(self):
        df = self.fetcher.fetch_history("INFY", period="1y")
        assert len(df) >= 200
        assert "Close" in df.columns
        assert "Volume" in df.columns
        assert df["Close"].iloc[-1] > 0

    def test_fetch_fundamentals(self):
        data = self.fetcher.fetch_fundamentals("TCS")
        assert data.symbol == "TCS"
        assert data.pe_ratio is not None and data.pe_ratio > 0

    def test_fetch_news(self):
        news = self.fetcher.fetch_news("RELIANCE")
        # News may or may not be available
        assert isinstance(news, list)
