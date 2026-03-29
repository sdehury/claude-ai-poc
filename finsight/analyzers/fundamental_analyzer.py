from finsight.models.stock import FundamentalData, FundamentalScore
from finsight.utils.helpers import score_linear, average_non_none, data_coverage


# Scoring thresholds: (bad_value, good_value)
# score_linear maps linearly: bad -> 0, good -> 100

EARNINGS_THRESHOLDS = {
    "roe": (0, 25),
    "revenue_growth_3y_cagr": (0, 20),
    "profit_growth_3y_cagr": (0, 25),
    "eps_growth_5y_cagr": (0, 20),
    "net_profit_margin": (0, 20),
}

BALANCE_SHEET_THRESHOLDS = {
    "debt_to_equity": (200, 0),       # Lower is better (yfinance reports as %)
    "current_ratio": (0.5, 2.0),
    "interest_coverage": (1.0, 10.0),
}

VALUATION_THRESHOLDS = {
    "pe_ratio": (50, 10),             # Lower is better
    "pb_ratio": (10, 1),              # Lower is better
    "ev_ebitda": (40, 8),             # Lower is better
    "peg_ratio": (3.0, 0.5),         # Lower is better
}

MOAT_THRESHOLDS = {
    "roce": (5, 25),
    "roe": (5, 25),
}

MANAGEMENT_THRESHOLDS = {
    "promoter_holding": (20, 75),
    "promoter_holding_change_qoq": (-5, 2),
    "dividend_yield": (0, 3),
}

# Category weights from FinancialDesign.MD
WEIGHTS = {
    "earnings_quality": 0.25,
    "balance_sheet": 0.20,
    "valuation": 0.20,
    "moat": 0.20,
    "management": 0.15,
}

RED_FLAG_PENALTY = 5  # Points deducted per red flag


class FundamentalAnalyzer:
    """Weighted fundamental scoring engine (0-100)."""

    def analyze(self, data: FundamentalData) -> FundamentalScore:
        """Compute comprehensive fundamental score with sub-scores."""
        earnings_score = self._score_earnings(data)
        balance_score = self._score_balance_sheet(data)
        valuation_score = self._score_valuation(data)
        moat_score = self._score_moat(data)
        management_score = self._score_management(data)

        # Weighted overall score
        overall = (
            earnings_score * WEIGHTS["earnings_quality"]
            + balance_score * WEIGHTS["balance_sheet"]
            + valuation_score * WEIGHTS["valuation"]
            + moat_score * WEIGHTS["moat"]
            + management_score * WEIGHTS["management"]
        )

        # Detect red flags and apply penalty
        red_flags = self._detect_red_flags(data)
        overall = max(0, overall - len(red_flags) * RED_FLAG_PENALTY)

        # Generate bull/bear points
        bull_points = self._generate_bull_points(data)
        bear_points = self._generate_bear_points(data)

        # Rating
        rating = self._compute_rating(overall)

        # Data coverage
        all_metrics = [
            data.pe_ratio, data.pb_ratio, data.roe, data.roce,
            data.debt_to_equity, data.current_ratio, data.interest_coverage,
            data.revenue_growth_3y_cagr, data.profit_growth_3y_cagr,
            data.eps_growth_5y_cagr, data.dividend_yield, data.promoter_holding,
            data.ev_ebitda, data.peg_ratio, data.free_cash_flow,
            data.net_profit_margin,
        ]
        coverage = data_coverage(all_metrics)

        return FundamentalScore(
            symbol=data.symbol,
            overall_score=round(overall, 1),
            earnings_quality_score=round(earnings_score, 1),
            balance_sheet_score=round(balance_score, 1),
            valuation_score=round(valuation_score, 1),
            moat_score=round(moat_score, 1),
            management_score=round(management_score, 1),
            red_flags=red_flags,
            bull_points=bull_points,
            bear_points=bear_points,
            rating=rating,
            data_coverage_pct=round(coverage, 1),
        )

    def _score_earnings(self, data: FundamentalData) -> float:
        scores = [
            score_linear(data.roe, *EARNINGS_THRESHOLDS["roe"]),
            score_linear(data.revenue_growth_3y_cagr, *EARNINGS_THRESHOLDS["revenue_growth_3y_cagr"]),
            score_linear(data.profit_growth_3y_cagr, *EARNINGS_THRESHOLDS["profit_growth_3y_cagr"]),
            score_linear(data.eps_growth_5y_cagr, *EARNINGS_THRESHOLDS["eps_growth_5y_cagr"]),
            score_linear(data.net_profit_margin, *EARNINGS_THRESHOLDS["net_profit_margin"]),
        ]
        return average_non_none(scores)

    def _score_balance_sheet(self, data: FundamentalData) -> float:
        scores = [
            score_linear(data.debt_to_equity, *BALANCE_SHEET_THRESHOLDS["debt_to_equity"]),
            score_linear(data.current_ratio, *BALANCE_SHEET_THRESHOLDS["current_ratio"]),
            score_linear(data.interest_coverage, *BALANCE_SHEET_THRESHOLDS["interest_coverage"]),
        ]
        return average_non_none(scores)

    def _score_valuation(self, data: FundamentalData) -> float:
        scores = [
            score_linear(data.pe_ratio, *VALUATION_THRESHOLDS["pe_ratio"]) if data.pe_ratio and data.pe_ratio > 0 else None,
            score_linear(data.pb_ratio, *VALUATION_THRESHOLDS["pb_ratio"]),
            score_linear(data.ev_ebitda, *VALUATION_THRESHOLDS["ev_ebitda"]),
            score_linear(data.peg_ratio, *VALUATION_THRESHOLDS["peg_ratio"]),
        ]
        base_score = average_non_none(scores)

        # Sector-relative P/E adjustment
        if data.pe_ratio and data.sector_pe and data.sector_pe > 0:
            ratio = data.pe_ratio / data.sector_pe
            if ratio < 0.8:
                base_score = min(100, base_score + 20)
            elif ratio > 1.2:
                base_score = max(0, base_score - 20)

        return base_score

    def _score_moat(self, data: FundamentalData) -> float:
        growth_min = None
        if data.revenue_growth_3y_cagr is not None and data.profit_growth_3y_cagr is not None:
            growth_min = min(data.revenue_growth_3y_cagr, data.profit_growth_3y_cagr)
        elif data.revenue_growth_3y_cagr is not None:
            growth_min = data.revenue_growth_3y_cagr
        elif data.profit_growth_3y_cagr is not None:
            growth_min = data.profit_growth_3y_cagr

        scores = [
            score_linear(data.roce, *MOAT_THRESHOLDS["roce"]),
            score_linear(data.roe, *MOAT_THRESHOLDS["roe"]),
            score_linear(growth_min, 0, 20) if growth_min is not None else None,
        ]
        return average_non_none(scores)

    def _score_management(self, data: FundamentalData) -> float:
        scores = [
            score_linear(data.promoter_holding, *MANAGEMENT_THRESHOLDS["promoter_holding"]),
            score_linear(data.promoter_holding_change_qoq, *MANAGEMENT_THRESHOLDS["promoter_holding_change_qoq"]),
            score_linear(data.dividend_yield, *MANAGEMENT_THRESHOLDS["dividend_yield"]),
        ]
        return average_non_none(scores)

    def _detect_red_flags(self, data: FundamentalData) -> list[str]:
        flags = []
        if data.debt_to_equity is not None and data.debt_to_equity > 200:
            flags.append(f"High debt-to-equity ratio: {data.debt_to_equity:.1f}%")
        if data.roe is not None and data.roe < 5:
            flags.append(f"Low ROE: {data.roe:.1f}%")
        if data.pe_ratio is not None and data.pe_ratio > 100:
            flags.append(f"Extremely high P/E: {data.pe_ratio:.1f}")
        if data.promoter_holding is not None and data.promoter_holding < 25:
            flags.append(f"Low promoter holding: {data.promoter_holding:.1f}%")
        if data.promoter_holding_change_qoq is not None and data.promoter_holding_change_qoq < -3:
            flags.append(f"Significant promoter stake reduction: {data.promoter_holding_change_qoq:.1f}pp QoQ")
        if data.interest_coverage is not None and data.interest_coverage < 1.5:
            flags.append(f"Weak interest coverage: {data.interest_coverage:.2f}x")
        if data.current_ratio is not None and data.current_ratio < 0.8:
            flags.append(f"Low current ratio: {data.current_ratio:.2f}")
        return flags

    def _generate_bull_points(self, data: FundamentalData) -> list[str]:
        points = []
        if data.roe is not None and data.roe > 15:
            points.append(f"Strong ROE of {data.roe:.1f}%")
        if data.roce is not None and data.roce > 15:
            points.append(f"High ROCE of {data.roce:.1f}%")
        if data.revenue_growth_3y_cagr is not None and data.revenue_growth_3y_cagr > 15:
            points.append(f"Robust revenue growth: {data.revenue_growth_3y_cagr:.1f}% 3Y CAGR")
        if data.profit_growth_3y_cagr is not None and data.profit_growth_3y_cagr > 15:
            points.append(f"Strong profit growth: {data.profit_growth_3y_cagr:.1f}% 3Y CAGR")
        if data.debt_to_equity is not None and data.debt_to_equity < 50:
            points.append(f"Low leverage with D/E of {data.debt_to_equity:.1f}%")
        if data.current_ratio is not None and data.current_ratio > 1.5:
            points.append(f"Healthy liquidity: current ratio {data.current_ratio:.2f}")
        if data.dividend_yield is not None and data.dividend_yield > 2:
            points.append(f"Attractive dividend yield: {data.dividend_yield:.2f}%")
        if data.free_cash_flow is not None and data.free_cash_flow > 0:
            points.append("Positive free cash flow generation")
        if data.promoter_holding is not None and data.promoter_holding > 60:
            points.append(f"High promoter confidence: {data.promoter_holding:.1f}% holding")
        if data.net_profit_margin is not None and data.net_profit_margin > 15:
            points.append(f"Healthy profit margins: {data.net_profit_margin:.1f}%")
        return points

    def _generate_bear_points(self, data: FundamentalData) -> list[str]:
        points = []
        if data.pe_ratio is not None and data.pe_ratio > 40:
            points.append(f"Expensive valuation at {data.pe_ratio:.1f}x P/E")
        if data.pb_ratio is not None and data.pb_ratio > 5:
            points.append(f"High price-to-book of {data.pb_ratio:.1f}x")
        if data.debt_to_equity is not None and data.debt_to_equity > 100:
            points.append(f"Elevated debt levels: D/E {data.debt_to_equity:.1f}%")
        if data.revenue_growth_3y_cagr is not None and data.revenue_growth_3y_cagr < 5:
            points.append(f"Sluggish revenue growth: {data.revenue_growth_3y_cagr:.1f}% 3Y CAGR")
        if data.roe is not None and data.roe < 10:
            points.append(f"Below-average ROE: {data.roe:.1f}%")
        if data.net_profit_margin is not None and data.net_profit_margin < 5:
            points.append(f"Thin profit margins: {data.net_profit_margin:.1f}%")
        if data.ev_ebitda is not None and data.ev_ebitda > 30:
            points.append(f"High EV/EBITDA of {data.ev_ebitda:.1f}x")
        if data.peg_ratio is not None and data.peg_ratio > 2:
            points.append(f"PEG ratio of {data.peg_ratio:.2f} suggests overvaluation relative to growth")
        return points

    @staticmethod
    def _compute_rating(score: float) -> str:
        if score >= 80:
            return "STRONG"
        elif score >= 65:
            return "GOOD"
        elif score >= 45:
            return "AVERAGE"
        elif score >= 30:
            return "WEAK"
        else:
            return "AVOID"
