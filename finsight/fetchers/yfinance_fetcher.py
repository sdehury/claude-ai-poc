import yfinance as yf
import pandas as pd
from typing import Optional
from datetime import datetime

from finsight.models.stock import StockQuote, FundamentalData
from finsight.utils.helpers import nse_symbol, cagr
from finsight.utils.logger import get_logger

logger = get_logger(__name__)


class YFinanceFetcher:
    """Primary data fetcher using Yahoo Finance API."""

    def fetch_quote(self, symbol: str) -> StockQuote:
        """Fetch current stock quote and basic info."""
        yf_symbol = nse_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info

        return StockQuote(
            symbol=symbol.upper(),
            name=info.get("longName") or info.get("shortName"),
            exchange=info.get("exchange", "NSE"),
            cmp=info.get("currentPrice") or info.get("regularMarketPrice", 0),
            high_52w=info.get("fiftyTwoWeekHigh"),
            low_52w=info.get("fiftyTwoWeekLow"),
            market_cap=info.get("marketCap"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            currency=info.get("currency", "INR"),
        )

    def fetch_history(
        self,
        symbol: str,
        period: str = "10y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data.

        Returns DataFrame with columns: Open, High, Low, Close, Volume
        and a DatetimeIndex.
        """
        yf_symbol = nse_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise ValueError(f"No history data for {yf_symbol}")

        # Keep only OHLCV columns
        cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        return df[cols]

    def fetch_fundamentals(self, symbol: str) -> FundamentalData:
        """Extract fundamental metrics from yfinance info and financials."""
        yf_symbol = nse_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info

        # Extract basic ratios from info dict
        roe = info.get("returnOnEquity")
        if roe is not None:
            roe = roe * 100  # Convert from decimal to percentage

        dividend_yield = info.get("dividendYield")
        if dividend_yield is not None:
            dividend_yield = dividend_yield * 100
            # yfinance sometimes returns absurd values for Indian stocks
            if dividend_yield > 20:
                dividend_yield = None

        # Compute revenue and profit CAGR from financial statements
        revenue_cagr_3y = self._compute_metric_cagr(ticker, "Total Revenue", 3)
        profit_cagr_3y = self._compute_metric_cagr(ticker, "Net Income", 3)

        # EPS growth from earnings history
        eps_cagr_5y = self._compute_eps_cagr(ticker, 5)

        # Net profit margin
        npm = info.get("profitMargins")
        if npm is not None:
            npm = npm * 100

        return FundamentalData(
            symbol=symbol.upper(),
            pe_ratio=info.get("trailingPE"),
            pb_ratio=info.get("priceToBook"),
            roe=roe,
            roce=None,  # Not available from yfinance
            debt_to_equity=info.get("debtToEquity"),
            current_ratio=info.get("currentRatio"),
            interest_coverage=None,  # Not directly available
            revenue_growth_3y_cagr=revenue_cagr_3y,
            profit_growth_3y_cagr=profit_cagr_3y,
            eps_growth_5y_cagr=eps_cagr_5y,
            dividend_yield=dividend_yield,
            promoter_holding=None,  # Not available from yfinance
            promoter_holding_change_qoq=None,
            fii_holding=None,
            dii_holding=None,
            free_cash_flow=info.get("freeCashflow"),
            ev_ebitda=info.get("enterpriseToEbitda"),
            peg_ratio=info.get("pegRatio"),
            sector_pe=None,  # Would need sector-level aggregation
            book_value=info.get("bookValue"),
            market_cap=info.get("marketCap"),
            net_profit_margin=npm,
        )

    def _compute_metric_cagr(
        self, ticker: yf.Ticker, metric_name: str, years: int
    ) -> Optional[float]:
        """Compute CAGR for a financial statement metric."""
        try:
            financials = ticker.financials
            if financials is None or financials.empty:
                return None

            if metric_name not in financials.index:
                return None

            row = financials.loc[metric_name].dropna()
            if len(row) < 2:
                return None

            # Columns are most-recent-first
            recent = row.iloc[0]
            # Take the value 'years' ago or the oldest available
            idx = min(years, len(row) - 1)
            older = row.iloc[idx]

            actual_years = idx  # Number of annual periods between the two
            if actual_years == 0:
                return None

            return cagr(abs(older), abs(recent), actual_years)
        except Exception as e:
            logger.debug(f"Could not compute {metric_name} CAGR: {e}")
            return None

    def _compute_eps_cagr(
        self, ticker: yf.Ticker, years: int
    ) -> Optional[float]:
        """Compute EPS CAGR from earnings data."""
        try:
            financials = ticker.financials
            if financials is None or financials.empty:
                return None

            # Try to get Net Income and shares outstanding
            if "Net Income" not in financials.index:
                return None

            net_income = financials.loc["Net Income"].dropna()
            if len(net_income) < 2:
                return None

            # Use net income as proxy for EPS growth (shares typically stable)
            recent = net_income.iloc[0]
            idx = min(years, len(net_income) - 1)
            older = net_income.iloc[idx]

            if older <= 0 or recent <= 0:
                return None

            return cagr(older, recent, idx)
        except Exception as e:
            logger.debug(f"Could not compute EPS CAGR: {e}")
            return None

    def fetch_news(self, symbol: str) -> list[dict]:
        """Fetch recent news headlines for a stock."""
        yf_symbol = nse_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        try:
            news = ticker.news or []
            return [
                {
                    "title": item.get("title", ""),
                    "publisher": item.get("publisher", ""),
                    "link": item.get("link", ""),
                    "published": item.get("providerPublishTime", ""),
                }
                for item in news[:20]
            ]
        except Exception:
            return []
