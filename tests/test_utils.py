from finsight.utils.helpers import (
    nse_symbol, cagr, score_linear, average_non_none, data_coverage,
    format_inr, format_pct,
)


class TestNseSymbol:
    def test_adds_ns_suffix(self):
        assert nse_symbol("RELIANCE") == "RELIANCE.NS"

    def test_does_not_double_suffix(self):
        assert nse_symbol("RELIANCE.NS") == "RELIANCE.NS"

    def test_respects_bse_suffix(self):
        assert nse_symbol("RELIANCE.BO") == "RELIANCE.BO"

    def test_uppercases(self):
        assert nse_symbol("reliance") == "RELIANCE.NS"

    def test_strips_whitespace(self):
        assert nse_symbol("  INFY  ") == "INFY.NS"


class TestCagr:
    def test_basic_cagr(self):
        result = cagr(100, 200, 5)
        assert abs(result - 14.87) < 0.1  # ~14.87%

    def test_zero_start(self):
        assert cagr(0, 200, 5) is None

    def test_negative_start(self):
        assert cagr(-100, 200, 5) is None

    def test_zero_years(self):
        assert cagr(100, 200, 0) is None


class TestScoreLinear:
    def test_at_good_value(self):
        assert score_linear(25, 0, 25) == 100.0

    def test_at_bad_value(self):
        assert score_linear(0, 0, 25) == 0.0

    def test_midpoint(self):
        assert score_linear(12.5, 0, 25) == 50.0

    def test_inverted_lower_is_better(self):
        # D/E: bad=2.0, good=0.0 → lower is better
        assert score_linear(0, 2, 0) == 100.0
        assert score_linear(2, 2, 0) == 0.0

    def test_clamped_above(self):
        assert score_linear(50, 0, 25) == 100.0

    def test_clamped_below(self):
        assert score_linear(-10, 0, 25) == 0.0

    def test_none_returns_none(self):
        assert score_linear(None, 0, 25) is None

    def test_equal_good_bad(self):
        assert score_linear(5, 10, 10) == 50.0


class TestAverageNonNone:
    def test_basic(self):
        assert average_non_none([60, 80, 100]) == 80.0

    def test_with_nones(self):
        assert average_non_none([60, None, 100]) == 80.0

    def test_all_none(self):
        assert average_non_none([None, None]) == 50.0

    def test_empty(self):
        assert average_non_none([]) == 50.0


class TestDataCoverage:
    def test_full(self):
        assert data_coverage([1, 2, 3]) == 100.0

    def test_partial(self):
        result = data_coverage([1, None, 3])
        assert abs(result - (2 / 3 * 100)) < 0.01

    def test_empty(self):
        assert data_coverage([]) == 0.0


class TestFormatInr:
    def test_crores(self):
        assert "Cr" in format_inr(50000000)

    def test_lakhs(self):
        assert "L" in format_inr(500000)

    def test_none(self):
        assert format_inr(None) == "N/A"


class TestFormatPct:
    def test_basic(self):
        assert format_pct(15.5) == "15.50%"

    def test_none(self):
        assert format_pct(None) == "N/A"
