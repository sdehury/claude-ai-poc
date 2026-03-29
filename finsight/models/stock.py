from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class StockQuote(BaseModel):
    symbol: str
    name: Optional[str] = None
    exchange: str = "NSE"
    cmp: float = Field(description="Current market price")
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    market_cap: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str = "INR"
    fetched_at: datetime = Field(default_factory=datetime.now)


class FundamentalData(BaseModel):
    symbol: str
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = Field(None, description="Return on Equity (%)")
    roce: Optional[float] = Field(None, description="Return on Capital Employed (%)")
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None
    revenue_growth_3y_cagr: Optional[float] = Field(None, description="3Y Revenue CAGR (%)")
    profit_growth_3y_cagr: Optional[float] = Field(None, description="3Y Net Profit CAGR (%)")
    eps_growth_5y_cagr: Optional[float] = Field(None, description="5Y EPS CAGR (%)")
    dividend_yield: Optional[float] = Field(None, description="Dividend yield (%)")
    promoter_holding: Optional[float] = Field(None, description="Promoter holding (%)")
    promoter_holding_change_qoq: Optional[float] = Field(None, description="QoQ change in promoter holding (pp)")
    fii_holding: Optional[float] = None
    dii_holding: Optional[float] = None
    free_cash_flow: Optional[float] = None
    ev_ebitda: Optional[float] = None
    peg_ratio: Optional[float] = None
    sector_pe: Optional[float] = None
    book_value: Optional[float] = None
    market_cap: Optional[float] = None
    net_profit_margin: Optional[float] = None
    fetched_at: datetime = Field(default_factory=datetime.now)


class FundamentalScore(BaseModel):
    symbol: str
    overall_score: float = Field(ge=0, le=100)
    earnings_quality_score: float = Field(ge=0, le=100)
    balance_sheet_score: float = Field(ge=0, le=100)
    valuation_score: float = Field(ge=0, le=100)
    moat_score: float = Field(ge=0, le=100)
    management_score: float = Field(ge=0, le=100)
    red_flags: list[str] = Field(default_factory=list)
    bull_points: list[str] = Field(default_factory=list)
    bear_points: list[str] = Field(default_factory=list)
    rating: str = Field(description="STRONG / GOOD / AVERAGE / WEAK / AVOID")
    data_coverage_pct: float = Field(
        description="Percentage of metrics that had actual data (vs None)"
    )


class TechnicalSignals(BaseModel):
    symbol: str
    cmp: float
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_20: Optional[float] = None
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bbands_upper: Optional[float] = None
    bbands_middle: Optional[float] = None
    bbands_lower: Optional[float] = None
    adx: Optional[float] = None
    trend: str = "NEUTRAL"
    momentum: str = "NEUTRAL"
    golden_cross: bool = False
    death_cross: bool = False
    price_vs_200dma_pct: Optional[float] = None
    relative_strength_vs_nifty: Optional[float] = None
    signals: list[str] = Field(default_factory=list)
