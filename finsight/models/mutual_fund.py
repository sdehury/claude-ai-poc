from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class MutualFundScheme(BaseModel):
    scheme_code: str
    scheme_name: str
    amc: Optional[str] = None
    category: Optional[str] = None
    nav: Optional[float] = None
    nav_date: Optional[str] = None


class MFReturns(BaseModel):
    return_1y: Optional[float] = Field(None, description="1-year absolute return (%)")
    return_3y_cagr: Optional[float] = Field(None, description="3-year CAGR (%)")
    return_5y_cagr: Optional[float] = Field(None, description="5-year CAGR (%)")
    return_10y_cagr: Optional[float] = Field(None, description="10-year CAGR (%)")


class MFAnalysisResult(BaseModel):
    scheme_code: str
    scheme_name: str
    latest_nav: float
    nav_date: str
    returns: MFReturns
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    std_deviation: Optional[float] = Field(None, description="Annualized std deviation (%)")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown (%)")
    max_drawdown_duration_days: Optional[int] = None
    rolling_returns_3y: Optional[list[dict]] = Field(
        None, description="List of {date, return_pct} for rolling 3Y returns"
    )
    overall_score: float = Field(ge=0, le=100)
    rating: str
    analysis_date: datetime = Field(default_factory=datetime.now)


class MFOverlapResult(BaseModel):
    fund_a_name: str
    fund_b_name: str
    overlap_pct: float = Field(description="Jaccard similarity (%)")
    common_stocks: list[str]
    fund_a_only: list[str]
    fund_b_only: list[str]
    classification: str = Field(description="LOW / MODERATE / HIGH")
