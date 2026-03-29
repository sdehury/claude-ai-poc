from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from finsight.models.stock import FundamentalScore, TechnicalSignals
from finsight.models.mutual_fund import MFAnalysisResult


class AdvisoryReport(BaseModel):
    ticker: str
    asset_type: str = Field(description="EQUITY or MUTUAL_FUND")
    overall_score: float
    recommendation: str
    executive_summary: Optional[str] = None
    investment_horizon: str = "5-10 years"
    suggested_allocation_pct: Optional[str] = None
    entry_zones: list[str] = Field(default_factory=list)
    target_5y: Optional[str] = None
    bull_case: list[str] = Field(default_factory=list)
    bear_case: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    macro_tailwinds: list[str] = Field(default_factory=list)
    macro_headwinds: list[str] = Field(default_factory=list)
    fundamental_score: Optional[FundamentalScore] = None
    technical_signals: Optional[TechnicalSignals] = None
    mf_analysis: Optional[MFAnalysisResult] = None
    generated_at: datetime = Field(default_factory=datetime.now)
    llm_generated: bool = False
    disclaimer: str = (
        "This analysis is for educational and research purposes only. "
        "It does not constitute financial advice. Always consult a "
        "SEBI-registered investment advisor before making investment decisions."
    )
