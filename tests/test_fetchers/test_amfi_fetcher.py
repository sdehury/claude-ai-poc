import pytest
from finsight.fetchers.amfi_fetcher import AMFIFetcher


@pytest.mark.integration
class TestAMFIFetcher:
    """Integration tests that hit real AMFI API."""

    def setup_method(self):
        self.fetcher = AMFIFetcher()

    def test_fetch_nav_history(self):
        # 122639 = Parag Parikh Flexi Cap Fund - Direct Growth
        nav_df, meta = self.fetcher.fetch_nav_history("122639")
        assert len(nav_df) > 1000  # Should have several years of data
        assert "nav" in nav_df.columns
        assert nav_df["nav"].iloc[-1] > 0
        assert meta.get("scheme_name") is not None

    def test_search_schemes(self):
        results = self.fetcher.search_schemes("parag parikh")
        assert len(results) > 0
        assert any("parag" in s.scheme_name.lower() for s in results)

    def test_fetch_scheme_details(self):
        details = self.fetcher.fetch_scheme_details("122639")
        assert details.scheme_code == "122639"
        assert details.nav is not None
        assert details.nav > 0

    def teardown_method(self):
        self.fetcher.close()
