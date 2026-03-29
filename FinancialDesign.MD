# FinSight — Long-Term Investment Analysis System
### Python-Based Equity & Mutual Fund Research Platform

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Data Sources & Integration](#3-data-sources--integration)
4. [Analysis Modules](#4-analysis-modules)
5. [Expert Advisory Engine](#5-expert-advisory-engine)
6. [Project Structure](#6-project-structure)
7. [Tech Stack](#7-tech-stack)
8. [Module Designs](#8-module-designs)
9. [Data Flow](#9-data-flow)
10. [Sample Output & Reports](#10-sample-output--reports)
11. [Roadmap](#11-roadmap)

---

## 1. System Overview

FinSight is a Python-based investment research platform designed for **long-term investment planning (5–10 years)**. Users input a list of stocks or mutual funds; the system fetches, aggregates, and analyzes data from multiple financial portals, applies macro-economic and geopolitical context, and produces an AI-assisted expert advisory report.

### Goals
- Deep-dive fundamental + technical analysis of stocks
- Mutual fund performance, portfolio overlap, and risk-adjusted returns
- Macro intelligence: trade wars, central bank policies, geopolitical triggers
- LLM-powered advisory narrative with bull/bear cases
- Long-term horizon scoring (5–10Y outlook)

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLI / Web UI                               │
│              (User inputs: Stocks, MFs, Horizon, Risk Profile)      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                 ┌───────────▼──────────┐
                 │   Orchestrator Layer  │
                 │  (main.py / FastAPI)  │
                 └─┬──────────┬─────────┘
                   │          │
       ┌───────────▼──┐  ┌────▼──────────────┐
       │  Data Fetcher │  │  Analysis Engine   │
       │   (scrapers,  │  │  (fundamentals,    │
       │   APIs, feeds)│  │   technicals, MF)  │
       └───────┬───────┘  └────────┬──────────┘
               │                   │
       ┌───────▼───────────────────▼──────────┐
       │           Data Store                  │
       │  SQLite / PostgreSQL + Redis cache    │
       └───────────────────┬──────────────────┘
                           │
              ┌────────────▼──────────────┐
              │  Macro Intelligence Layer  │
              │  (news, geo-politics,      │
              │   policies, trade data)    │
              └────────────┬──────────────┘
                           │
              ┌────────────▼──────────────┐
              │   Advisory Engine (LLM)   │
              │  GPT-4 / Claude / Gemini  │
              └────────────┬──────────────┘
                           │
              ┌────────────▼──────────────┐
              │   Report Generator        │
              │   PDF / HTML / JSON       │
              └───────────────────────────┘
```

---

## 3. Data Sources & Integration

### 3.1 Stock Data Sources

| Source | What to Fetch | Method |
|---|---|---|
| **Screener.in** | P/E, P/B, ROE, ROCE, Sales growth, Profit growth, Debt, Promoter holding, Quarterly results | Web scraping (`requests` + `BeautifulSoup`) or unofficial API |
| **NSE / Nifty India** | Live price, 52W high/low, circuit limits, index composition, FII/DII data | `nsepy` library or `nsetools`, NSE official JSON endpoints |
| **BSE India** | Corporate actions, announcements, board meetings, shareholding pattern | BSE REST API / scraping |
| **MoneyControl** | Analyst recommendations, broker target prices, news sentiment, MF data | Scraping + RSS feeds |
| **Yahoo Finance** | Historical OHLCV, dividends, splits | `yfinance` Python library |
| **Bloomberg / Reuters** | Global macro, commodity prices, forex, bond yields | `bloomberg-blpapi` (terminal required) or free Bloomberg RSS; Reuters news API |
| **Investing.com** | Economic calendar, global indices, futures | Scraping / `investpy` |
| **AMFI India** | Mutual Fund NAV, scheme details, AUM | AMFI REST API (free, official) |
| **Value Research** | MF ratings, category returns, portfolio holdings | Scraping |
| **RBI / SEBI** | Regulatory announcements, policy rates, FII limits | RBI official data API, SEBI circulars |

### 3.2 Macro / Geopolitical Sources

| Source | Data | Method |
|---|---|---|
| **World Bank API** | GDP, inflation, trade balance per country | REST API (free) |
| **IMF Data** | Global growth forecasts, debt/GDP | REST API (free) |
| **US Fed / RBI / ECB** | Policy rate decisions, minutes | Official press release scraping |
| **GDELT Project** | Geopolitical event scoring, news tone by country | Free bulk data download |
| **NewsAPI / GNews** | Financial news with sentiment tagging | REST API (free tier) |
| **Twitter / X** | Real-time sentiment on stocks/sectors | Twitter API v2 |
| **Quandl / FRED** | Macro time series: oil, gold, VIX, DXY, US 10Y yield | `quandl` / `pandas_datareader` |

---

## 4. Analysis Modules

### 4.1 Fundamental Analysis Module

```
Inputs  : Company ticker(s)
Outputs : Score (0–100), Bull/Bear thesis, Red flags

Metrics analyzed:
  Revenue Growth (3Y CAGR, 5Y CAGR)
  Net Profit Margin trend
  Return on Equity (ROE) ≥ 15% threshold
  Return on Capital Employed (ROCE) ≥ 15%
  Debt-to-Equity Ratio
  Interest Coverage Ratio
  Free Cash Flow Yield
  Promoter Holding % (increasing = positive signal)
  FII / DII holding trends
  P/E vs sector P/E
  PEG Ratio (P/E ÷ growth)
  EV/EBITDA
  Dividend yield & payout ratio
  Working capital efficiency
```

**Scoring Framework:**

| Category | Weight |
|---|---|
| Earnings Quality & Growth | 25% |
| Balance Sheet Strength | 20% |
| Valuation (relative & absolute) | 20% |
| Management & Governance | 15% |
| Competitive Moat Indicators | 20% |

---

### 4.2 Technical Analysis Module

```
Library: ta-lib or pandas-ta

Indicators:
  Trend    : SMA (50, 200), EMA (20, 50), ADX, Supertrend
  Momentum : RSI (14), MACD, Stochastic
  Volume   : OBV, Volume MA, Delivery %
  Volatility: Bollinger Bands, ATR
  Support/Resistance: Pivot Points, Fibonacci retracement

Long-term signals (weekly/monthly charts):
  Golden Cross (50W SMA crossing above 200W SMA)
  Price vs 200-DMA position
  52-week relative strength vs Nifty
```

---

### 4.3 Mutual Fund Analysis Module

```
Inputs  : Fund name / ISIN / AMC
Outputs : Score, Peer comparison, Portfolio overlap report

Metrics:
  1Y / 3Y / 5Y / 10Y absolute & category-relative returns
  Alpha (vs benchmark)
  Beta (market sensitivity)
  Sharpe Ratio (risk-adjusted return)
  Sortino Ratio (downside deviation)
  Standard Deviation
  Rolling returns (12M, 36M)
  Max Drawdown
  Portfolio Turnover Ratio
  Expense Ratio
  AUM size & trend
  Fund Manager tenure & track record
  Portfolio concentration (top 10 holdings %)
  Sector & market-cap allocation
  Overlap analysis between two funds (Jaccard similarity)
```

---

### 4.4 Macro & Sector Intelligence Module

```
Analyzes:
  Interest Rate Cycle (RBI, US Fed trajectory)
  Inflation trend (CPI, WPI India; CPI US)
  INR/USD exchange rate trend
  Oil price impact (import-heavy vs export sectors)
  India GDP growth trajectory
  Government Capex & budget allocation by sector
  PLI Scheme beneficiary sectors
  China+1 theme impact
  US-China trade war: beneficiary Indian sectors
  Global supply chain shifts
  FII flows into India (monthly)

Sector scoring based on macro tailwinds:
  IT / Software  : USD strength, US tech spending
  Banking / NBFC : Rate cycle, credit growth, NPA cycle
  Pharma         : US FDA pipeline, domestic formulations
  Auto           : EV transition, PLI, commodity prices
  Infra / Cement : Budget capex, housing cycle
  FMCG           : Rural recovery, inflation pass-through
  Energy / PSU   : Oil price, green energy policy
  Metals         : China demand, global supply
```

---

### 4.5 Geopolitical Risk Scoring Module

```
Factors tracked:
  India-Pakistan / India-China border tension index
  Russia-Ukraine war: commodity & energy price impact
  US-China decoupling: semiconductor, supply chain
  Middle East instability: oil price volatility
  Trade partner health: US, EU, China, ASEAN GDP
  Sanctions impact on trade routes
  BRICS expansion & de-dollarization trend
  WTO disputes affecting Indian exports

Risk Score Output:
  Global Risk Index (0–10)
  India-specific Risk Delta
  Sector-level exposure to geopolitical risk
```

---

## 5. Expert Advisory Engine

### 5.1 LLM Integration

The advisory engine uses an LLM (Claude / GPT-4 / Gemini) to synthesize all module outputs into a human-readable investment thesis.

**System Prompt Design:**
```
You are a senior equity research analyst and portfolio manager with 20 years
of experience in Indian and global markets. Given the structured analysis data
below, produce an investment advisory report with:
  1. Executive Summary
  2. Bull Case (3 strong reasons to invest)
  3. Bear Case (3 key risks)
  4. Suggested Allocation (% of portfolio)
  5. Entry Strategy (lump sum vs SIP, price zones)
  6. 5-Year Price Target (DCF + peer multiple based)
  7. Red Flags to monitor
  8. Comparison with peer stocks/funds in the same category
```

### 5.2 Advisory Output Structure

```json
{
  "ticker": "RELIANCE",
  "overall_score": 78,
  "investment_horizon": "7-10 years",
  "recommendation": "BUY on dips",
  "suggested_allocation": "8-10% of equity portfolio",
  "entry_zones": ["2400-2500 INR"],
  "5y_target": "4800-5200 INR",
  "bull_case": ["Jio financial services growth", "Retail expansion", "Green energy pivot"],
  "bear_case": ["High capex / debt cycle", "Regulatory risk in telecom", "Global oil price dependency"],
  "macro_tailwinds": ["India digital growth", "PLI beneficiary", "USD earning diversification"],
  "geopolitical_risk": "LOW",
  "red_flags": ["Promoter pledge levels", "Execution on new energy timeline"],
  "peer_comparison": {...}
}
```

---

## 6. Project Structure

```
finance/
├── FinancialDesign.MD              # This design document
│
├── main.py                         # CLI entry point
├── app.py                          # FastAPI web server (optional)
├── config.yaml                     # API keys, thresholds, settings
├── requirements.txt
│
├── fetchers/                       # Data acquisition layer
│   ├── __init__.py
│   ├── screener_fetcher.py         # Screener.in scraper
│   ├── nse_fetcher.py              # NSE/Nifty data
│   ├── yfinance_fetcher.py         # Yahoo Finance OHLCV
│   ├── amfi_fetcher.py             # Mutual fund NAV + data
│   ├── moneycontrol_fetcher.py     # News, analyst targets
│   ├── macro_fetcher.py            # World Bank, IMF, FRED, RBI
│   ├── news_fetcher.py             # NewsAPI, RSS, GDELT
│   └── base_fetcher.py             # Base class with rate limiting
│
├── analyzers/                      # Analysis engine
│   ├── __init__.py
│   ├── fundamental_analyzer.py     # Ratio analysis, scoring
│   ├── technical_analyzer.py       # TA indicators (pandas-ta)
│   ├── mf_analyzer.py              # MF risk-return metrics
│   ├── macro_analyzer.py           # Sector + macro scoring
│   ├── sentiment_analyzer.py       # News NLP sentiment
│   └── geopolitical_analyzer.py    # Geo-risk scoring
│
├── advisory/                       # LLM advisory layer
│   ├── __init__.py
│   ├── prompt_builder.py           # Constructs LLM prompts
│   ├── advisor.py                  # Calls LLM API, parses output
│   └── portfolio_advisor.py        # Multi-stock portfolio view
│
├── models/                         # Data models
│   ├── stock.py                    # Stock dataclass
│   ├── mutual_fund.py              # MF dataclass
│   └── report.py                   # Report schema
│
├── storage/                        # Persistence
│   ├── db.py                       # SQLAlchemy ORM setup
│   ├── cache.py                    # Redis / file-based cache
│   └── migrations/
│
├── reports/                        # Report generation
│   ├── pdf_generator.py            # ReportLab / WeasyPrint
│   ├── html_generator.py           # Jinja2 HTML templates
│   └── templates/
│       ├── stock_report.html
│       └── mf_report.html
│
├── utils/
│   ├── logger.py
│   ├── rate_limiter.py
│   └── helpers.py
│
└── tests/
    ├── test_fetchers.py
    ├── test_analyzers.py
    └── test_advisory.py
```

---

## 7. Tech Stack

| Layer | Library / Tool |
|---|---|
| **Language** | Python 3.11+ |
| **HTTP / Scraping** | `requests`, `httpx`, `BeautifulSoup4`, `playwright` (JS-heavy sites) |
| **Stock Data** | `yfinance`, `nsepy`, `nsetools`, `investpy` |
| **MF Data** | AMFI REST API, `mftool` library |
| **Technical Analysis** | `pandas-ta`, `ta-lib`, `numpy` |
| **Data Processing** | `pandas`, `numpy`, `scipy` |
| **NLP / Sentiment** | `transformers` (FinBERT), `textblob`, `vaderSentiment` |
| **LLM Advisory** | `anthropic` (Claude API) or `openai` (GPT-4) |
| **Database** | SQLite (dev), PostgreSQL (prod) via `SQLAlchemy` |
| **Caching** | `redis` / `diskcache` |
| **Scheduling** | `APScheduler` (auto-refresh data daily) |
| **API Server** | `FastAPI` + `uvicorn` |
| **CLI** | `click` or `typer` |
| **Reports** | `reportlab`, `weasyprint`, `jinja2`, `plotly` |
| **Visualization** | `plotly`, `matplotlib`, `seaborn` |
| **Config** | `pydantic-settings`, `python-dotenv` |
| **Testing** | `pytest`, `pytest-asyncio` |

---

## 8. Module Designs

### 8.1 Screener.in Fetcher

```python
# fetchers/screener_fetcher.py

class ScreenerFetcher(BaseFetcher):
    BASE_URL = "https://www.screener.in/company/{ticker}/consolidated/"

    def fetch(self, ticker: str) -> dict:
        """
        Returns: {
          'pe': float, 'pb': float, 'roe': float, 'roce': float,
          'debt_equity': float, 'promoter_holding': float,
          'revenue_growth_3y': float, 'profit_growth_3y': float,
          'eps_growth_5y': float, 'free_cash_flow': float,
          'quarterly_results': [...]
        }
        """
```

### 8.2 NSE Fetcher

```python
# fetchers/nse_fetcher.py

class NSEFetcher(BaseFetcher):
    # Uses nsepy + NSE JSON endpoints:
    # https://www.nseindia.com/api/quote-equity?symbol={SYMBOL}
    # https://www.nseindia.com/api/index-names  (for Nifty indices)

    def fetch_stock_quote(self, symbol: str) -> dict: ...
    def fetch_fii_dii_data(self) -> pd.DataFrame: ...
    def fetch_index_data(self, index: str = "NIFTY 50") -> pd.DataFrame: ...
    def fetch_derivative_data(self, symbol: str) -> dict: ...
```

### 8.3 Fundamental Analyzer

```python
# analyzers/fundamental_analyzer.py

class FundamentalAnalyzer:
    WEIGHTS = {
        'earnings_quality': 0.25,
        'balance_sheet': 0.20,
        'valuation': 0.20,
        'management': 0.15,
        'moat': 0.20
    }

    def score(self, data: dict) -> FundamentalScore:
        """Returns score 0–100 with sub-scores and red flags."""

    def _score_earnings(self, data) -> float:
        # Revenue CAGR, profit CAGR, EPS consistency, FCF conversion

    def _score_balance_sheet(self, data) -> float:
        # D/E ratio, interest coverage, current ratio, pledging %

    def _score_valuation(self, data) -> float:
        # P/E vs sector, PEG, EV/EBITDA vs 5Y average

    def _detect_red_flags(self, data) -> list[str]:
        # Declining margins, rising debt, promoter selling, auditor change
```

### 8.4 MF Analyzer

```python
# analyzers/mf_analyzer.py

class MFAnalyzer:
    def analyze(self, scheme_code: str) -> MFReport:
        nav_history = self.fetcher.get_nav_history(scheme_code)
        benchmark   = self.fetcher.get_benchmark_returns(scheme_code)

        return MFReport(
            returns    = self._compute_returns(nav_history),
            alpha      = self._compute_alpha(nav_history, benchmark),
            beta       = self._compute_beta(nav_history, benchmark),
            sharpe     = self._compute_sharpe(nav_history),
            sortino    = self._compute_sortino(nav_history),
            max_drawdown = self._compute_max_drawdown(nav_history),
            rolling_returns = self._compute_rolling(nav_history),
        )

    def overlap_analysis(self, scheme_a: str, scheme_b: str) -> float:
        """Returns portfolio overlap % between two funds."""
```

### 8.5 Advisory Engine

```python
# advisory/advisor.py

class InvestmentAdvisor:
    def __init__(self, llm_client):
        self.llm = llm_client  # Anthropic or OpenAI client

    def generate_report(self,
                        ticker: str,
                        fundamental: FundamentalScore,
                        technical: TechnicalSignals,
                        macro: MacroContext,
                        news_sentiment: SentimentScore) -> AdvisoryReport:

        prompt = PromptBuilder.build(
            ticker, fundamental, technical, macro, news_sentiment
        )
        response = self.llm.complete(prompt)
        return AdvisoryReport.parse(response)
```

---

## 9. Data Flow

```
User Input: ["RELIANCE", "INFY", "HDFC Bank", "Parag Parikh Flexi Cap"]
      │
      ▼
Orchestrator dispatches parallel fetch tasks
      │
      ├──► Screener Fetcher     → Fundamentals data
      ├──► NSE Fetcher          → Live price, FII/DII, corporate actions
      ├──► yFinance Fetcher     → 10Y OHLCV history
      ├──► AMFI Fetcher         → NAV history (for MFs)
      ├──► News Fetcher         → Last 90 days news, RSS feeds
      ├──► Macro Fetcher        → RBI rate, CPI, GDP, US Fed rate
      └──► Geo-Risk Fetcher     → GDELT events, trade data
      │
      ▼
All data stored in SQLite / PostgreSQL with timestamp
      │
      ▼
Analysis Engine runs on stored data
      ├── Fundamental Analyzer  → Score + thesis
      ├── Technical Analyzer    → Entry/exit signals
      ├── MF Analyzer           → Risk-return metrics
      ├── Macro Analyzer        → Sector tailwind score
      ├── Sentiment Analyzer    → News sentiment score
      └── Geopolitical Analyzer → Risk score
      │
      ▼
Advisory Engine (LLM) receives structured JSON of all scores
      │
      ▼
Report Generator produces:
  ├── PDF report (for each stock/fund)
  ├── Portfolio-level HTML dashboard
  └── JSON data export (for further use)
```

---

## 10. Sample Output & Reports

### Stock Report Summary (Console)

```
═══════════════════════════════════════════════════════════
  RELIANCE INDUSTRIES LTD (RELIANCE.NS)
  CMP: ₹2,456  |  52W H/L: ₹3,020 / ₹2,180
═══════════════════════════════════════════════════════════
  FUNDAMENTAL SCORE    : 78/100  ✅ STRONG
  TECHNICAL SIGNAL     : NEUTRAL (Consolidating near 200DMA)
  NEWS SENTIMENT       : POSITIVE (0.72 / 1.0)
  MACRO TAILWIND       : HIGH  (Digital India, Green Energy)
  GEOPOLITICAL RISK    : LOW

  RECOMMENDATION       : BUY ON DIPS (₹2,300–2,400 zone)
  5-YEAR TARGET        : ₹4,800–5,200 (90–110% upside)
  SUGGESTED ALLOCATION : 8–10% of equity portfolio

  BULL CASE:
    → Jio Financial Services — underpenetrated BFSI play
    → Reliance Retail — capturing India consumption story
    → Green energy capex will dominate by 2027

  BEAR CASE:
    → High capital intensity in new verticals
    → Refining margin compression on lower crude spreads
    → Regulatory scrutiny in telecom / competition from Airtel

  RED FLAGS TO MONITOR:
    ⚠ Promoter pledge levels (check quarterly)
    ⚠ New energy execution timeline delays
═══════════════════════════════════════════════════════════
```

### Mutual Fund Comparison Table

```
Fund Name                       | 1Y    | 3Y    | 5Y    | Sharpe | Alpha | Rating
──────────────────────────────────────────────────────────────────────────────────
Parag Parikh Flexi Cap          | 18.2% | 22.1% | 19.8% | 1.42   | +4.2  | ★★★★★
Mirae Asset Large Cap           | 14.1% | 16.8% | 15.2% | 1.18   | +1.8  | ★★★★
PPFAS vs Mirae Overlap          | 34%  (moderate overlap — acceptable for diversification)
```

---

## 11. Roadmap

### Phase 1 — Foundation (Weeks 1–3)
- [ ] Set up project skeleton and config
- [ ] Build `yfinance` + `nsepy` fetchers (reliable, no scraping needed)
- [ ] Build AMFI MF fetcher (free official API)
- [ ] Implement fundamental analyzer with Screener scraper
- [ ] Basic CLI: input tickers, output fundamental scores

### Phase 2 — Analysis Depth (Weeks 4–6)
- [ ] Technical analysis module (pandas-ta)
- [ ] MF risk-return analyzer (Sharpe, Alpha, drawdown)
- [ ] News fetcher + FinBERT sentiment scoring
- [ ] Macro data fetcher (World Bank, FRED APIs)
- [ ] SQLite storage + caching layer

### Phase 3 — Intelligence Layer (Weeks 7–9)
- [ ] Geopolitical risk scoring (GDELT)
- [ ] Sector macro scoring
- [ ] LLM advisory integration (Claude / GPT-4)
- [ ] Portfolio-level view (correlation, overlap, diversification score)

### Phase 4 — Reports & UI (Weeks 10–12)
- [ ] PDF + HTML report generation
- [ ] Plotly charts (price history, returns, peer comparison)
- [ ] FastAPI web server with simple dashboard
- [ ] APScheduler for daily data refresh
- [ ] Watchlist alerts (email / Telegram)

### Future Enhancements
- Options data analysis for hedging suggestions
- SIP return simulator with goal planning
- Multi-currency support (US stocks, ETFs)
- Portfolio backtesting engine
- Telegram / WhatsApp bot interface

---

## Key Investment Frameworks Applied

### For Stocks (5–10Y Horizon)
1. **QGLP Framework** (Quality, Growth, Longevity, Price) — Motilal Oswal style
2. **Moat Analysis** — Brand, switching costs, network effects, cost advantage
3. **Business Cycle Positioning** — Where is the sector in its cycle?
4. **Management Quality Check** — Capital allocation history, related-party transactions
5. **DCF Valuation** — 10-year cash flow projection with conservative assumptions

### For Mutual Funds
1. **Rolling Returns** over 3/5/7 year periods (not point-to-point)
2. **Consistency Score** — How often does fund beat its benchmark?
3. **Downside Protection** — Max drawdown, recovery time
4. **Portfolio Quality** — Underlying stocks quality, concentration risk
5. **Fund House Reputation** — AUM stability, manager turnover history

---

## Risk Disclaimers (System Output)

> All analysis generated by FinSight is for **educational and research purposes only**.
> It does not constitute financial advice. Investment in securities markets is subject
> to market risks. Past performance does not guarantee future results. Always consult
> a SEBI-registered investment advisor before making investment decisions.

---

*Last Updated: 2026-03-28 | FinSight v0.1 Design Document*
