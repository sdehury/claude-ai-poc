from typing import Optional
from finsight.models.report import AdvisoryReport
from finsight.utils.logger import get_logger

logger = get_logger(__name__)


class PortfolioAdvisor:
    """Multi-asset portfolio-level analysis and recommendations."""

    @staticmethod
    def analyze_portfolio(reports: list[AdvisoryReport]) -> dict:
        """Analyze a collection of stock/MF reports as a portfolio.

        Returns portfolio-level metrics and diversification assessment.
        """
        if not reports:
            return {"error": "No reports to analyze"}

        equity_reports = [r for r in reports if r.asset_type == "EQUITY"]
        mf_reports = [r for r in reports if r.asset_type == "MUTUAL_FUND"]

        # Portfolio score (weighted average)
        total_score = sum(r.overall_score for r in reports)
        avg_score = total_score / len(reports)

        # Sector distribution (for equities)
        sectors = {}
        for r in equity_reports:
            if r.fundamental_score:
                # We don't have sector in FundamentalScore, use from technical
                pass
            sectors[r.ticker] = r.overall_score

        # Collect all red flags
        all_red_flags = []
        for r in reports:
            for flag in r.red_flags:
                all_red_flags.append(f"[{r.ticker}] {flag}")

        # Score distribution
        strong = sum(1 for r in reports if r.overall_score >= 65)
        average = sum(1 for r in reports if 45 <= r.overall_score < 65)
        weak = sum(1 for r in reports if r.overall_score < 45)

        # Concentration risk
        concentration_warning = None
        if len(reports) < 3:
            concentration_warning = "Portfolio is concentrated — consider adding more positions for diversification"
        elif len(equity_reports) > 0 and len(mf_reports) == 0:
            concentration_warning = "Portfolio has only equities — consider adding mutual funds for diversification"

        return {
            "num_positions": len(reports),
            "num_equities": len(equity_reports),
            "num_mutual_funds": len(mf_reports),
            "portfolio_score": round(avg_score, 1),
            "score_distribution": {
                "strong": strong,
                "average": average,
                "weak": weak,
            },
            "all_red_flags": all_red_flags,
            "concentration_warning": concentration_warning,
            "recommendations": PortfolioAdvisor._generate_recommendations(
                reports, avg_score
            ),
        }

    @staticmethod
    def _generate_recommendations(reports: list[AdvisoryReport], avg_score: float) -> list[str]:
        recs = []

        weak_positions = [r.ticker for r in reports if r.overall_score < 40]
        if weak_positions:
            recs.append(f"Review weak positions: {', '.join(weak_positions)}")

        strong_positions = [r.ticker for r in reports if r.overall_score >= 75]
        if strong_positions:
            recs.append(f"Strong conviction picks: {', '.join(strong_positions)}")

        if avg_score >= 65:
            recs.append("Portfolio overall quality is GOOD — maintain positions")
        elif avg_score >= 45:
            recs.append("Portfolio quality is AVERAGE — consider upgrading weaker positions")
        else:
            recs.append("Portfolio quality needs improvement — review all positions")

        return recs
