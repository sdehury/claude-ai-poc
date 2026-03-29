from typing import Optional

from finsight.fetchers.yfinance_fetcher import YFinanceFetcher
from finsight.fetchers.amfi_fetcher import AMFIFetcher
from finsight.fetchers.macro_fetcher import MacroFetcher
from finsight.fetchers.news_fetcher import NewsFetcher
from finsight.analyzers.fundamental_analyzer import FundamentalAnalyzer
from finsight.analyzers.technical_analyzer import TechnicalAnalyzer
from finsight.analyzers.mf_analyzer import MFAnalyzer
from finsight.analyzers.sentiment_analyzer import SentimentAnalyzer
from finsight.analyzers.macro_analyzer import MacroAnalyzer
from finsight.advisory.advisor import InvestmentAdvisor
from finsight.storage.db import Database
from finsight.storage.cache import Cache
from finsight.models.report import AdvisoryReport
from finsight.models.mutual_fund import MFAnalysisResult
from finsight.utils.logger import get_logger

logger = get_logger(__name__)


class Orchestrator:
    """Pipeline coordinator: fetch → analyze → advise → report."""

    def __init__(
        self,
        skip_advisory: bool = False,
        skip_technical: bool = False,
        api_key: Optional[str] = None,
    ):
        self.yf_fetcher = YFinanceFetcher()
        self.amfi_fetcher = AMFIFetcher()
        self.macro_fetcher = MacroFetcher()
        self.news_fetcher = NewsFetcher()

        self.fundamental_analyzer = FundamentalAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        self.mf_analyzer = MFAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.macro_analyzer = MacroAnalyzer()

        self.skip_advisory = skip_advisory
        self.skip_technical = skip_technical
        self.advisor = None if skip_advisory else InvestmentAdvisor(api_key=api_key)
        self.db = Database()
        self.cache = Cache()

    def analyze_equity(self, symbol: str) -> AdvisoryReport:
        """Run full equity analysis pipeline."""
        logger.info(f"Analyzing equity: {symbol}")

        # Step 1: Fetch data
        logger.info("Fetching stock quote...")
        quote = self.yf_fetcher.fetch_quote(symbol)

        logger.info("Fetching fundamentals...")
        fundamentals = self.yf_fetcher.fetch_fundamentals(symbol)

        logger.info("Fetching price history...")
        history = self.yf_fetcher.fetch_history(symbol)

        # Step 2: Fundamental analysis
        logger.info("Running fundamental analysis...")
        fund_score = self.fundamental_analyzer.analyze(fundamentals)

        # Step 3: Technical analysis (optional)
        tech_signals = None
        if not self.skip_technical:
            try:
                logger.info("Running technical analysis...")
                # Fetch Nifty data for relative strength
                nifty_df = None
                try:
                    nifty_df = self.yf_fetcher.fetch_history("^NSEI", period="2y")
                except Exception:
                    logger.debug("Could not fetch Nifty data for relative strength")

                tech_signals = self.technical_analyzer.analyze(
                    history, symbol, nifty_df
                )
            except Exception as e:
                logger.warning(f"Technical analysis failed: {e}")

        # Step 4: Sentiment analysis
        sentiment = None
        try:
            logger.info("Analyzing news sentiment...")
            news = self.yf_fetcher.fetch_news(symbol)
            if news:
                headlines = [n["title"] for n in news if n.get("title")]
                sentiment = self.sentiment_analyzer.analyze_texts(headlines)
        except Exception as e:
            logger.debug(f"Sentiment analysis skipped: {e}")

        # Step 5: Macro analysis
        macro = None
        if quote.sector:
            try:
                logger.info(f"Analyzing macro environment for {quote.sector}...")
                macro_data = self.cache.get("macro_indicators")
                if macro_data is None:
                    macro_data = self.macro_fetcher.fetch_global_indicators()
                    if macro_data:
                        self.cache.set("macro_indicators", macro_data)
                macro = self.macro_analyzer.analyze_sector(quote.sector, macro_data)
            except Exception as e:
                logger.debug(f"Macro analysis skipped: {e}")

        # Step 6: Advisory report
        if not self.skip_advisory and self.advisor:
            logger.info("Generating LLM advisory report...")
            report = self.advisor.generate_equity_report(
                quote, fund_score, tech_signals, sentiment, macro
            )
        else:
            logger.info("Generating basic report (no LLM)...")
            report = AdvisoryReport(
                ticker=quote.symbol,
                asset_type="EQUITY",
                overall_score=fund_score.overall_score,
                recommendation=self._auto_recommendation(fund_score.overall_score),
                executive_summary=(
                    f"{quote.name or quote.symbol} scores {fund_score.overall_score}/100 "
                    f"({fund_score.rating}) on fundamental analysis. "
                    f"Data coverage: {fund_score.data_coverage_pct}%."
                ),
                bull_case=fund_score.bull_points,
                bear_case=fund_score.bear_points,
                red_flags=fund_score.red_flags,
                macro_tailwinds=macro.get("tailwinds", []) if macro else [],
                macro_headwinds=macro.get("headwinds", []) if macro else [],
                fundamental_score=fund_score,
                technical_signals=tech_signals,
            )

        # Save to database
        try:
            self.db.save_report(report)
        except Exception as e:
            logger.debug(f"Could not save report to DB: {e}")

        return report

    def analyze_mf(
        self,
        scheme_code: str,
        benchmark_ticker: str = "^NSEI",
    ) -> MFAnalysisResult:
        """Run mutual fund analysis pipeline."""
        logger.info(f"Analyzing mutual fund: {scheme_code}")

        # Fetch NAV history
        logger.info("Fetching NAV history...")
        nav_df, meta = self.amfi_fetcher.fetch_nav_history(scheme_code)
        scheme_name = meta.get("scheme_name", f"Scheme {scheme_code}")

        # Fetch benchmark data
        benchmark_df = None
        try:
            logger.info("Fetching benchmark data...")
            benchmark_df = self.yf_fetcher.fetch_history(
                benchmark_ticker, period="10y"
            )
        except Exception as e:
            logger.warning(f"Could not fetch benchmark: {e}")

        # Run analysis
        logger.info("Running MF analysis...")
        result = self.mf_analyzer.analyze(
            nav_df, scheme_name, scheme_code, benchmark_df
        )

        return result

    def search_mf(self, query: str) -> list[dict]:
        """Search for mutual fund schemes."""
        schemes = self.amfi_fetcher.search_schemes(query)
        return [
            {"code": s.scheme_code, "name": s.scheme_name}
            for s in schemes
        ]

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

    def close(self):
        """Clean up resources."""
        self.macro_fetcher.close()
        self.news_fetcher.close()
        self.cache.close()
