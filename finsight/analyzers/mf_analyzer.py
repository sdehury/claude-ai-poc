import pandas as pd
import numpy as np
from typing import Optional

from finsight.models.mutual_fund import MFAnalysisResult, MFReturns, MFOverlapResult
from finsight.utils.helpers import cagr, score_linear, average_non_none
from finsight.utils.logger import get_logger

logger = get_logger(__name__)

RISK_FREE_RATE = 0.07  # India 10Y govt bond ~7%
TRADING_DAYS = 252


class MFAnalyzer:
    """Mutual fund risk-return analysis engine."""

    def analyze(
        self,
        nav_df: pd.DataFrame,
        scheme_name: str,
        scheme_code: str,
        benchmark_df: Optional[pd.DataFrame] = None,
        risk_free_rate: float = RISK_FREE_RATE,
    ) -> MFAnalysisResult:
        """Perform comprehensive MF analysis.

        Args:
            nav_df: DataFrame with DatetimeIndex and 'nav' column
            scheme_name: Fund name
            scheme_code: AMFI scheme code
            benchmark_df: Optional benchmark OHLCV (e.g., Nifty 50)
            risk_free_rate: Annual risk-free rate (decimal)
        """
        nav = nav_df["nav"].astype(float)
        daily_returns = nav.pct_change().dropna()

        # Returns
        returns = self._compute_returns(nav)

        # Risk metrics
        ann_return = daily_returns.mean() * TRADING_DAYS
        ann_std = daily_returns.std() * np.sqrt(TRADING_DAYS)

        # Sharpe ratio
        sharpe = (ann_return - risk_free_rate) / ann_std if ann_std > 0 else None

        # Sortino ratio (downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(TRADING_DAYS)
        sortino = (ann_return - risk_free_rate) / downside_std if downside_std > 0 else None

        # Alpha and Beta (require benchmark)
        alpha, beta = self._compute_alpha_beta(
            daily_returns, benchmark_df, risk_free_rate
        )

        # Max drawdown
        max_dd, max_dd_duration = self._compute_max_drawdown(nav)

        # Rolling 3Y returns
        rolling_3y = self._compute_rolling_returns(nav, years=3)

        # Composite score
        score = self._compute_composite_score(
            sharpe, sortino, alpha, max_dd,
            returns.return_3y_cagr, returns.return_5y_cagr,
        )
        rating = self._compute_rating(score)

        return MFAnalysisResult(
            scheme_code=scheme_code,
            scheme_name=scheme_name,
            latest_nav=round(float(nav.iloc[-1]), 4),
            nav_date=str(nav.index[-1].date()),
            returns=returns,
            sharpe_ratio=self._safe_round(sharpe, 3),
            sortino_ratio=self._safe_round(sortino, 3),
            alpha=self._safe_round(alpha, 2),
            beta=self._safe_round(beta, 3),
            std_deviation=self._safe_round(ann_std * 100, 2),
            max_drawdown=self._safe_round(max_dd, 2),
            max_drawdown_duration_days=max_dd_duration,
            rolling_returns_3y=rolling_3y,
            overall_score=round(score, 1),
            rating=rating,
        )

    def _compute_returns(self, nav: pd.Series) -> MFReturns:
        """Compute absolute and CAGR returns for various periods."""
        n = len(nav)

        return_1y = None
        if n >= TRADING_DAYS:
            return_1y = ((nav.iloc[-1] / nav.iloc[-TRADING_DAYS]) - 1) * 100

        return_3y = None
        if n >= 3 * TRADING_DAYS:
            return_3y = cagr(
                nav.iloc[-3 * TRADING_DAYS], nav.iloc[-1], 3
            )

        return_5y = None
        if n >= 5 * TRADING_DAYS:
            return_5y = cagr(
                nav.iloc[-5 * TRADING_DAYS], nav.iloc[-1], 5
            )

        return_10y = None
        if n >= 10 * TRADING_DAYS:
            return_10y = cagr(
                nav.iloc[-10 * TRADING_DAYS], nav.iloc[-1], 10
            )

        return MFReturns(
            return_1y=self._safe_round(return_1y, 2),
            return_3y_cagr=self._safe_round(return_3y, 2),
            return_5y_cagr=self._safe_round(return_5y, 2),
            return_10y_cagr=self._safe_round(return_10y, 2),
        )

    def _compute_alpha_beta(
        self,
        fund_returns: pd.Series,
        benchmark_df: Optional[pd.DataFrame],
        risk_free_rate: float,
    ) -> tuple[Optional[float], Optional[float]]:
        """Compute Jensen's Alpha and Beta against a benchmark."""
        if benchmark_df is None or benchmark_df.empty:
            return None, None

        bench_close = benchmark_df["Close"]
        bench_returns = bench_close.pct_change().dropna()

        # Align dates
        common_idx = fund_returns.index.intersection(bench_returns.index)
        if len(common_idx) < 60:  # Need at least ~3 months
            return None, None

        fr = fund_returns.loc[common_idx]
        br = bench_returns.loc[common_idx]

        # Beta = Cov(fund, bench) / Var(bench)
        covariance = fr.cov(br)
        bench_var = br.var()
        if bench_var == 0:
            return None, None

        beta = covariance / bench_var

        # Alpha = Fund annualized return - (Rf + Beta * (Bench annualized - Rf))
        fund_ann = fr.mean() * TRADING_DAYS
        bench_ann = br.mean() * TRADING_DAYS
        alpha = (fund_ann - (risk_free_rate + beta * (bench_ann - risk_free_rate))) * 100

        return alpha, beta

    @staticmethod
    def _compute_max_drawdown(nav: pd.Series) -> tuple[Optional[float], Optional[int]]:
        """Compute maximum drawdown and its duration in days."""
        if len(nav) < 2:
            return None, None

        cummax = nav.cummax()
        drawdown = (nav - cummax) / cummax
        max_dd = float(drawdown.min()) * 100

        # Duration: find the peak before max drawdown and recovery after
        trough_idx = drawdown.idxmin()
        peak_before = nav.loc[:trough_idx].idxmax()
        duration = (trough_idx - peak_before).days

        return max_dd, duration

    @staticmethod
    def _compute_rolling_returns(
        nav: pd.Series, years: int = 3, step_days: int = 21
    ) -> Optional[list[dict]]:
        """Compute rolling N-year returns at monthly intervals."""
        window = years * TRADING_DAYS
        if len(nav) < window + step_days:
            return None

        results = []
        indices = range(window, len(nav), step_days)

        for i in indices:
            end_val = nav.iloc[i]
            start_val = nav.iloc[i - window]
            if start_val > 0:
                ret = cagr(start_val, end_val, years)
                if ret is not None:
                    results.append({
                        "date": str(nav.index[i].date()),
                        "return_pct": round(ret, 2),
                    })

        return results if results else None

    def _compute_composite_score(
        self,
        sharpe: Optional[float],
        sortino: Optional[float],
        alpha: Optional[float],
        max_dd: Optional[float],
        cagr_3y: Optional[float],
        cagr_5y: Optional[float],
    ) -> float:
        """Compute weighted composite score (0-100).

        Weights:
        - Sharpe: 25%
        - Sortino: 15%
        - Alpha: 20%
        - Max Drawdown: 15%
        - 3Y CAGR: 15%
        - 5Y CAGR: 10%
        """
        scores_weights = [
            (score_linear(sharpe, 0.0, 1.5), 0.25),
            (score_linear(sortino, 0.0, 2.0), 0.15),
            (score_linear(alpha, -2.0, 5.0), 0.20),
            (score_linear(max_dd, -40.0, -10.0), 0.15),  # Less negative is better
            (score_linear(cagr_3y, 5.0, 20.0), 0.15),
            (score_linear(cagr_5y, 5.0, 18.0), 0.10),
        ]

        total_weight = 0
        weighted_sum = 0
        for score, weight in scores_weights:
            if score is not None:
                weighted_sum += score * weight
                total_weight += weight

        if total_weight == 0:
            return 50.0

        return weighted_sum / total_weight * (total_weight / 1.0)  # Normalize

    @staticmethod
    def _compute_rating(score: float) -> str:
        if score >= 80:
            return "EXCELLENT"
        elif score >= 65:
            return "GOOD"
        elif score >= 45:
            return "AVERAGE"
        elif score >= 30:
            return "BELOW AVERAGE"
        else:
            return "POOR"

    @staticmethod
    def overlap_analysis(
        fund_a_name: str,
        fund_a_holdings: list[str],
        fund_b_name: str,
        fund_b_holdings: list[str],
    ) -> MFOverlapResult:
        """Compute portfolio overlap between two funds using Jaccard similarity.

        Args:
            fund_a_holdings: List of stock names/tickers in fund A
            fund_b_holdings: List of stock names/tickers in fund B
        """
        set_a = {h.upper().strip() for h in fund_a_holdings}
        set_b = {h.upper().strip() for h in fund_b_holdings}

        common = set_a & set_b
        union = set_a | set_b

        overlap_pct = (len(common) / len(union) * 100) if union else 0

        if overlap_pct < 25:
            classification = "LOW"
        elif overlap_pct < 50:
            classification = "MODERATE"
        else:
            classification = "HIGH"

        return MFOverlapResult(
            fund_a_name=fund_a_name,
            fund_b_name=fund_b_name,
            overlap_pct=round(overlap_pct, 1),
            common_stocks=sorted(common),
            fund_a_only=sorted(set_a - set_b),
            fund_b_only=sorted(set_b - set_a),
            classification=classification,
        )

    @staticmethod
    def _safe_round(val: Optional[float], decimals: int = 2) -> Optional[float]:
        if val is None or np.isnan(val) or np.isinf(val):
            return None
        return round(float(val), decimals)
