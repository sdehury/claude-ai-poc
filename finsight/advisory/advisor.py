import json
import os
import re
from typing import Optional

from finsight.models.stock import StockQuote, FundamentalScore, TechnicalSignals
from finsight.models.mutual_fund import MFAnalysisResult
from finsight.models.report import AdvisoryReport
from finsight.advisory.prompt_builder import PromptBuilder
from finsight.utils.logger import get_logger

logger = get_logger(__name__)


class InvestmentAdvisor:
    """LLM-powered advisory engine using Claude API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set. Use --skip-advisory flag "
                    "or set the key in .env file."
                )
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def generate_equity_report(
        self,
        quote: StockQuote,
        fundamental: FundamentalScore,
        technical: Optional[TechnicalSignals] = None,
        sentiment: Optional[dict] = None,
        macro: Optional[dict] = None,
    ) -> AdvisoryReport:
        """Generate a comprehensive equity advisory report."""
        prompt = PromptBuilder.build_equity_prompt(
            quote, fundamental, technical, sentiment, macro
        )

        try:
            llm_response = self._call_llm(prompt)
            parsed = self._parse_json_response(llm_response)

            return AdvisoryReport(
                ticker=quote.symbol,
                asset_type="EQUITY",
                overall_score=fundamental.overall_score,
                recommendation=parsed.get("recommendation", self._auto_recommendation(fundamental.overall_score)),
                executive_summary=parsed.get("executive_summary"),
                investment_horizon=parsed.get("investment_horizon", "5-10 years"),
                suggested_allocation_pct=parsed.get("suggested_allocation_pct"),
                entry_zones=parsed.get("entry_zones", []),
                target_5y=parsed.get("target_5y"),
                bull_case=parsed.get("bull_case", fundamental.bull_points),
                bear_case=parsed.get("bear_case", fundamental.bear_points),
                red_flags=parsed.get("red_flags", fundamental.red_flags),
                macro_tailwinds=parsed.get("macro_tailwinds", []),
                macro_headwinds=parsed.get("macro_headwinds", []),
                fundamental_score=fundamental,
                technical_signals=technical,
                llm_generated=True,
            )
        except Exception as e:
            logger.warning(f"LLM advisory failed: {e}. Generating basic report.")
            return self._fallback_equity_report(quote, fundamental, technical)

    def generate_mf_report(
        self,
        analysis: MFAnalysisResult,
    ) -> AdvisoryReport:
        """Generate a mutual fund advisory report."""
        prompt = PromptBuilder.build_mf_prompt(analysis)

        try:
            llm_response = self._call_llm(prompt)
            parsed = self._parse_json_response(llm_response)

            return AdvisoryReport(
                ticker=analysis.scheme_code,
                asset_type="MUTUAL_FUND",
                overall_score=analysis.overall_score,
                recommendation=parsed.get("recommendation", self._auto_recommendation(analysis.overall_score)),
                executive_summary=parsed.get("executive_summary"),
                investment_horizon=parsed.get("investment_horizon", "5-10 years"),
                suggested_allocation_pct=parsed.get("suggested_allocation_pct"),
                bull_case=parsed.get("bull_case", []),
                bear_case=parsed.get("bear_case", []),
                red_flags=parsed.get("red_flags", []),
                macro_tailwinds=parsed.get("macro_tailwinds", []),
                mf_analysis=analysis,
                llm_generated=True,
            )
        except Exception as e:
            logger.warning(f"LLM advisory failed: {e}. Generating basic report.")
            return self._fallback_mf_report(analysis)

    def _call_llm(self, user_prompt: str) -> str:
        """Call the Claude API."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.3,
            system=PromptBuilder.get_system_prompt(),
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    @staticmethod
    def _parse_json_response(text: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Try to extract JSON from code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Try to find raw JSON
        brace_start = text.find("{")
        brace_end = text.rfind("}") + 1
        if brace_start >= 0 and brace_end > brace_start:
            return json.loads(text[brace_start:brace_end])

        raise ValueError("No valid JSON found in LLM response")

    @staticmethod
    def _auto_recommendation(score: float) -> str:
        if score >= 75:
            return "BUY"
        elif score >= 60:
            return "BUY ON DIPS"
        elif score >= 45:
            return "HOLD"
        elif score >= 30:
            return "REDUCE"
        else:
            return "AVOID"

    def _fallback_equity_report(
        self,
        quote: StockQuote,
        fundamental: FundamentalScore,
        technical: Optional[TechnicalSignals],
    ) -> AdvisoryReport:
        """Generate a report without LLM, using only analysis data."""
        return AdvisoryReport(
            ticker=quote.symbol,
            asset_type="EQUITY",
            overall_score=fundamental.overall_score,
            recommendation=self._auto_recommendation(fundamental.overall_score),
            executive_summary=(
                f"{quote.name or quote.symbol} scores {fundamental.overall_score}/100 "
                f"({fundamental.rating}) on fundamental analysis. "
                f"Data coverage: {fundamental.data_coverage_pct}%."
            ),
            bull_case=fundamental.bull_points,
            bear_case=fundamental.bear_points,
            red_flags=fundamental.red_flags,
            fundamental_score=fundamental,
            technical_signals=technical,
            llm_generated=False,
        )

    def _fallback_mf_report(self, analysis: MFAnalysisResult) -> AdvisoryReport:
        """Generate a MF report without LLM."""
        returns = analysis.returns
        summary_parts = [f"{analysis.scheme_name} scores {analysis.overall_score}/100 ({analysis.rating})."]
        if returns.return_3y_cagr is not None:
            summary_parts.append(f"3Y CAGR: {returns.return_3y_cagr}%.")
        if analysis.sharpe_ratio is not None:
            summary_parts.append(f"Sharpe: {analysis.sharpe_ratio}.")

        return AdvisoryReport(
            ticker=analysis.scheme_code,
            asset_type="MUTUAL_FUND",
            overall_score=analysis.overall_score,
            recommendation=self._auto_recommendation(analysis.overall_score),
            executive_summary=" ".join(summary_parts),
            mf_analysis=analysis,
            llm_generated=False,
        )
