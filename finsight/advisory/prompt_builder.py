import json
from typing import Optional

from finsight.models.stock import StockQuote, FundamentalScore, TechnicalSignals
from finsight.models.mutual_fund import MFAnalysisResult
from finsight.utils.helpers import format_inr, format_pct


SYSTEM_PROMPT = """You are a senior equity research analyst and portfolio manager with 20 years of experience in Indian and global markets. You specialize in long-term investment analysis (5-10 year horizon) for Indian equities and mutual funds.

Given the structured analysis data below, produce an investment advisory report in JSON format with these exact fields:
{
  "executive_summary": "2-3 sentence summary",
  "recommendation": "BUY / BUY ON DIPS / HOLD / REDUCE / AVOID",
  "investment_horizon": "e.g., 5-7 years",
  "suggested_allocation_pct": "e.g., 5-8% of equity portfolio",
  "entry_zones": ["price range 1", "price range 2"],
  "target_5y": "target price range with reasoning",
  "bull_case": ["reason 1", "reason 2", "reason 3"],
  "bear_case": ["risk 1", "risk 2", "risk 3"],
  "red_flags": ["flag 1"],
  "macro_tailwinds": ["tailwind 1"],
  "macro_headwinds": ["headwind 1"]
}

Be specific with numbers. Base your analysis on the data provided. Be balanced — present both opportunities and risks honestly. Think like a fiduciary advisor focused on capital preservation and long-term wealth creation."""


class PromptBuilder:
    """Constructs structured prompts for the LLM advisory engine."""

    @staticmethod
    def build_equity_prompt(
        quote: StockQuote,
        fundamental: FundamentalScore,
        technical: Optional[TechnicalSignals] = None,
        sentiment: Optional[dict] = None,
        macro: Optional[dict] = None,
    ) -> str:
        """Build a detailed equity analysis prompt."""
        sections = []

        # Stock overview
        sections.append(f"""## Stock Overview
- **Symbol**: {quote.symbol}
- **Name**: {quote.name or 'N/A'}
- **CMP**: {format_inr(quote.cmp)}
- **52W High/Low**: {format_inr(quote.high_52w)} / {format_inr(quote.low_52w)}
- **Market Cap**: {format_inr(quote.market_cap)}
- **Sector**: {quote.sector or 'N/A'}
- **Industry**: {quote.industry or 'N/A'}""")

        # Fundamental analysis
        sections.append(f"""## Fundamental Analysis (Score: {fundamental.overall_score}/100 — {fundamental.rating})
- **Earnings Quality**: {fundamental.earnings_quality_score}/100
- **Balance Sheet**: {fundamental.balance_sheet_score}/100
- **Valuation**: {fundamental.valuation_score}/100
- **Competitive Moat**: {fundamental.moat_score}/100
- **Management**: {fundamental.management_score}/100
- **Data Coverage**: {fundamental.data_coverage_pct}%

**Bull Points**: {'; '.join(fundamental.bull_points) if fundamental.bull_points else 'None identified'}
**Bear Points**: {'; '.join(fundamental.bear_points) if fundamental.bear_points else 'None identified'}
**Red Flags**: {'; '.join(fundamental.red_flags) if fundamental.red_flags else 'None'}""")

        # Technical analysis
        if technical:
            sections.append(f"""## Technical Analysis
- **Trend**: {technical.trend}
- **Momentum**: {technical.momentum}
- **RSI (14)**: {technical.rsi_14 or 'N/A'}
- **SMA 50**: {technical.sma_50 or 'N/A'} | SMA 200: {technical.sma_200 or 'N/A'}
- **Price vs 200-DMA**: {format_pct(technical.price_vs_200dma_pct)}
- **ADX**: {technical.adx or 'N/A'}
- **Golden Cross**: {'Yes' if technical.golden_cross else 'No'}
- **Death Cross**: {'Yes' if technical.death_cross else 'No'}

**Signals**: {'; '.join(technical.signals) if technical.signals else 'None'}""")

        # Sentiment
        if sentiment:
            sections.append(f"""## News Sentiment
- **Score**: {sentiment.get('score', 'N/A')} ({sentiment.get('label', 'N/A')})
- **Positive**: {sentiment.get('positive_pct', 0)}% | Negative: {sentiment.get('negative_pct', 0)}%
- **Articles Analyzed**: {sentiment.get('num_articles', 0)}""")

        # Macro
        if macro:
            sections.append(f"""## Macro Environment
- **Sector Macro Score**: {macro.get('macro_score', 'N/A')}/100 ({macro.get('assessment', 'N/A')})
- **Tailwinds**: {'; '.join(macro.get('tailwinds', []))}
- **Headwinds**: {'; '.join(macro.get('headwinds', []))}""")

        return "\n\n".join(sections) + "\n\nProvide your advisory report as a JSON object."

    @staticmethod
    def build_mf_prompt(analysis: MFAnalysisResult) -> str:
        """Build a mutual fund analysis prompt."""
        returns = analysis.returns
        return f"""## Mutual Fund Analysis

- **Fund**: {analysis.scheme_name}
- **Scheme Code**: {analysis.scheme_code}
- **Latest NAV**: ₹{analysis.latest_nav} (as of {analysis.nav_date})

### Returns
- **1Y Return**: {format_pct(returns.return_1y)}
- **3Y CAGR**: {format_pct(returns.return_3y_cagr)}
- **5Y CAGR**: {format_pct(returns.return_5y_cagr)}
- **10Y CAGR**: {format_pct(returns.return_10y_cagr)}

### Risk Metrics
- **Sharpe Ratio**: {analysis.sharpe_ratio or 'N/A'}
- **Sortino Ratio**: {analysis.sortino_ratio or 'N/A'}
- **Alpha**: {format_pct(analysis.alpha)}
- **Beta**: {analysis.beta or 'N/A'}
- **Std Deviation**: {format_pct(analysis.std_deviation)}
- **Max Drawdown**: {format_pct(analysis.max_drawdown)}

### Overall Score: {analysis.overall_score}/100 ({analysis.rating})

Provide your advisory report as a JSON object. Include SIP vs lump-sum recommendation."""

    @staticmethod
    def get_system_prompt() -> str:
        return SYSTEM_PROMPT
