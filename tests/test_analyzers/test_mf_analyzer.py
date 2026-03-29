import pytest
import numpy as np
from finsight.analyzers.mf_analyzer import MFAnalyzer


class TestMFAnalyzer:
    def setup_method(self):
        self.analyzer = MFAnalyzer()

    def test_analyze_produces_valid_result(self, sample_nav_df, sample_benchmark_df):
        result = self.analyzer.analyze(
            sample_nav_df, "Test Fund", "TEST001", sample_benchmark_df
        )
        assert result.scheme_name == "Test Fund"
        assert result.scheme_code == "TEST001"
        assert result.latest_nav > 0
        assert 0 <= result.overall_score <= 100

    def test_returns_computed(self, sample_nav_df):
        result = self.analyzer.analyze(sample_nav_df, "Test Fund", "TEST001")
        returns = result.returns
        assert returns.return_1y is not None
        assert returns.return_3y_cagr is not None
        assert returns.return_5y_cagr is not None

    def test_sharpe_ratio_range(self, sample_nav_df):
        result = self.analyzer.analyze(sample_nav_df, "Test Fund", "TEST001")
        if result.sharpe_ratio is not None:
            assert -5 <= result.sharpe_ratio <= 5

    def test_max_drawdown_negative(self, sample_nav_df):
        result = self.analyzer.analyze(sample_nav_df, "Test Fund", "TEST001")
        assert result.max_drawdown is not None
        assert result.max_drawdown <= 0

    def test_alpha_beta_with_benchmark(self, sample_nav_df, sample_benchmark_df):
        result = self.analyzer.analyze(
            sample_nav_df, "Test Fund", "TEST001", sample_benchmark_df
        )
        assert result.alpha is not None
        assert result.beta is not None
        # Beta should be positive for a fund tracking equities
        assert result.beta > 0

    def test_alpha_beta_without_benchmark(self, sample_nav_df):
        result = self.analyzer.analyze(sample_nav_df, "Test Fund", "TEST001")
        assert result.alpha is None
        assert result.beta is None

    def test_rolling_returns(self, sample_nav_df):
        result = self.analyzer.analyze(sample_nav_df, "Test Fund", "TEST001")
        assert result.rolling_returns_3y is not None
        assert len(result.rolling_returns_3y) > 0
        for entry in result.rolling_returns_3y:
            assert "date" in entry
            assert "return_pct" in entry

    def test_overlap_analysis(self):
        result = MFAnalyzer.overlap_analysis(
            "Fund A",
            ["RELIANCE", "TCS", "INFY", "HDFC", "ICICI"],
            "Fund B",
            ["TCS", "INFY", "WIPRO", "HCL", "ICICI"],
        )
        # 3 common (TCS, INFY, ICICI) out of 7 unique
        assert result.overlap_pct == pytest.approx(42.9, abs=0.1)
        assert len(result.common_stocks) == 3
        assert result.classification == "MODERATE"

    def test_overlap_no_overlap(self):
        result = MFAnalyzer.overlap_analysis(
            "Fund A", ["A", "B", "C"],
            "Fund B", ["D", "E", "F"],
        )
        assert result.overlap_pct == 0.0
        assert result.classification == "LOW"

    def test_overlap_full_overlap(self):
        result = MFAnalyzer.overlap_analysis(
            "Fund A", ["A", "B", "C"],
            "Fund B", ["A", "B", "C"],
        )
        assert result.overlap_pct == 100.0
        assert result.classification == "HIGH"

    def test_rating_thresholds(self):
        assert MFAnalyzer._compute_rating(85) == "EXCELLENT"
        assert MFAnalyzer._compute_rating(70) == "GOOD"
        assert MFAnalyzer._compute_rating(50) == "AVERAGE"
        assert MFAnalyzer._compute_rating(35) == "BELOW AVERAGE"
        assert MFAnalyzer._compute_rating(20) == "POOR"
