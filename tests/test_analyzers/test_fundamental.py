import pytest
from finsight.analyzers.fundamental_analyzer import FundamentalAnalyzer
from finsight.models.stock import FundamentalData


class TestFundamentalAnalyzer:
    def setup_method(self):
        self.analyzer = FundamentalAnalyzer()

    def test_strong_stock_scores_high(self, strong_stock_fundamentals):
        result = self.analyzer.analyze(strong_stock_fundamentals)
        assert result.overall_score >= 60
        assert result.rating in ("STRONG", "GOOD")
        assert len(result.bull_points) > 0

    def test_weak_stock_scores_low(self, weak_stock_fundamentals):
        result = self.analyzer.analyze(weak_stock_fundamentals)
        assert result.overall_score < 40
        assert result.rating in ("WEAK", "AVOID")
        assert len(result.red_flags) >= 2

    def test_sparse_data_does_not_crash(self, sparse_fundamentals):
        result = self.analyzer.analyze(sparse_fundamentals)
        assert 0 <= result.overall_score <= 100
        assert result.data_coverage_pct < 30  # Most fields are None

    def test_red_flags_high_debt(self):
        data = FundamentalData(symbol="DEBTCO", debt_to_equity=300)
        result = self.analyzer.analyze(data)
        assert any("debt" in f.lower() for f in result.red_flags)

    def test_red_flags_low_roe(self):
        data = FundamentalData(symbol="LOWROE", roe=2.0)
        result = self.analyzer.analyze(data)
        assert any("roe" in f.lower() for f in result.red_flags)

    def test_red_flags_high_pe(self):
        data = FundamentalData(symbol="EXPPCO", pe_ratio=150)
        result = self.analyzer.analyze(data)
        assert any("p/e" in f.lower() for f in result.red_flags)

    def test_red_flags_low_promoter(self):
        data = FundamentalData(symbol="LOWPRO", promoter_holding=15)
        result = self.analyzer.analyze(data)
        assert any("promoter" in f.lower() for f in result.red_flags)

    def test_score_range_always_valid(self, strong_stock_fundamentals, weak_stock_fundamentals, sparse_fundamentals):
        for data in [strong_stock_fundamentals, weak_stock_fundamentals, sparse_fundamentals]:
            result = self.analyzer.analyze(data)
            assert 0 <= result.overall_score <= 100
            assert 0 <= result.earnings_quality_score <= 100
            assert 0 <= result.balance_sheet_score <= 100
            assert 0 <= result.valuation_score <= 100
            assert 0 <= result.moat_score <= 100
            assert 0 <= result.management_score <= 100

    def test_bull_points_generated_for_strong_stock(self, strong_stock_fundamentals):
        result = self.analyzer.analyze(strong_stock_fundamentals)
        # Strong stock should have bull points about ROE, growth, etc.
        assert any("roe" in p.lower() for p in result.bull_points)

    def test_bear_points_generated_for_weak_stock(self, weak_stock_fundamentals):
        result = self.analyzer.analyze(weak_stock_fundamentals)
        assert any("valuation" in p.lower() or "p/e" in p.lower() for p in result.bear_points)

    def test_rating_thresholds(self):
        # Test each rating boundary
        for score, expected in [(85, "STRONG"), (70, "GOOD"), (50, "AVERAGE"), (35, "WEAK"), (15, "AVOID")]:
            rating = FundamentalAnalyzer._compute_rating(score)
            assert rating == expected

    def test_all_none_fields(self):
        """A stock with no data should still produce a valid result."""
        data = FundamentalData(symbol="EMPTY")
        result = self.analyzer.analyze(data)
        assert 0 <= result.overall_score <= 100
        assert result.data_coverage_pct == 0.0
