# FinSight - Long-Term Investment Analysis Platform

A Python-based investment research platform for **Indian equities and mutual funds** with a 5-10 year investment horizon. Fetches real financial data, runs fundamental/technical/macro analysis with validated scoring, and produces LLM-powered advisory reports.

## Features

- **Equity Analysis**: Fundamental scoring (0-100), technical indicators, sentiment analysis, macro context
- **Mutual Fund Analysis**: Risk-return metrics (Sharpe, Sortino, Alpha, Beta), rolling returns, drawdown analysis
- **MF Search**: Search AMFI database for mutual fund schemes by name
- **Portfolio View**: Multi-stock portfolio summary with diversification insights
- **LLM Advisory** (optional): Claude-powered investment thesis with bull/bear cases, 5Y targets
- **History**: SQLite-backed analysis history for past lookups

## Architecture

```
CLI (typer + Rich)
  |
  v
Orchestrator ── coordinates pipeline
  |
  ├── Fetchers ── yfinance, AMFI API, World Bank, RSS news
  ├── Analyzers ── fundamental, technical, MF, sentiment, macro
  ├── Advisory  ── Claude LLM integration (optional)
  └── Storage   ── SQLite + diskcache (24h TTL)
```

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd finance

# Install dependencies
pip install -r requirements.txt

# (Optional) Set up API keys for LLM advisory
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Usage

#### Analyze Stocks

```bash
# Basic analysis (fundamental + technical + sentiment + macro)
python main.py analyze-stock RELIANCE INFY TCS HDFCBANK

# Single stock
python main.py analyze-stock BANDHANBNK

# With LLM-powered advisory (requires ANTHROPIC_API_KEY in .env)
python main.py analyze-stock RELIANCE --with-advisory

# Skip technical analysis
python main.py analyze-stock RELIANCE --skip-technical

# JSON output
python main.py analyze-stock RELIANCE -o json
```

**Stock symbols** use NSE naming: `RELIANCE`, `HDFCBANK`, `INFY`, `TCS`, `ITC`, `NATIONALUM`, `VEDL`, `JIOFIN`, `BANKBARODA`, `IDFCFIRSTB`, `BANDHANBNK`, `UCOBANK`, etc.

#### Analyze Mutual Funds

```bash
# Search for scheme codes first
python main.py search-mf "parag parikh"
python main.py search-mf "mirae asset large cap"

# Analyze by scheme code (Direct Plan Growth variants)
python main.py analyze-mf 122639              # Parag Parikh Flexi Cap
python main.py analyze-mf 118834 118825       # Multiple funds

# Custom benchmark
python main.py analyze-mf 122639 --benchmark "^NSEI"
```

#### View History

```bash
python main.py history
python main.py history --limit 50
```

### Docker

```bash
# Build the image
docker build -t finsight .

# Run stock analysis
docker run --rm finsight analyze-stock RELIANCE INFY TCS

# Run with LLM advisory (pass API key)
docker run --rm -e ANTHROPIC_API_KEY=your_key finsight analyze-stock RELIANCE --with-advisory

# Run mutual fund analysis
docker run --rm finsight analyze-mf 122639

# Search mutual funds
docker run --rm finsight search-mf "mirae asset"

# Persist data across runs (history + cache)
docker run --rm -v finsight-data:/app/data -v finsight-cache:/app/cache finsight analyze-stock HDFCBANK
```

## Project Structure

```
finance/
├── main.py                          # CLI entry point (typer)
├── config.yaml                      # Thresholds, weights, API endpoints
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Build config + pytest settings
├── .env.example                     # Environment variable template
├── Dockerfile                       # Container image
│
├── finsight/                        # Main package
│   ├── orchestrator.py              # Pipeline coordinator
│   │
│   ├── fetchers/                    # Data acquisition
│   │   ├── base_fetcher.py          # ABC with rate limiting
│   │   ├── yfinance_fetcher.py      # PRIMARY: stock quotes, OHLCV, fundamentals
│   │   ├── amfi_fetcher.py          # Mutual fund NAV + scheme search
│   │   ├── macro_fetcher.py         # World Bank GDP, inflation
│   │   ├── news_fetcher.py          # RSS feeds (MoneyControl, ET)
│   │   └── nse_fetcher.py           # NSE API (best-effort)
│   │
│   ├── analyzers/                   # Analysis engines (all produce 0-100 scores)
│   │   ├── fundamental_analyzer.py  # Weighted: earnings 25%, BS 20%, valuation 20%, moat 20%, mgmt 15%
│   │   ├── technical_analyzer.py    # SMA, RSI, MACD, Bollinger, ADX via pandas-ta
│   │   ├── mf_analyzer.py           # Sharpe, Sortino, Alpha, Beta, drawdown, overlap
│   │   ├── sentiment_analyzer.py    # VADER sentiment on news
│   │   └── macro_analyzer.py        # Sector scoring based on GDP/inflation/rates
│   │
│   ├── advisory/                    # LLM-powered reports
│   │   ├── advisor.py               # Claude API integration + fallback
│   │   ├── prompt_builder.py        # Structured prompt construction
│   │   └── portfolio_advisor.py     # Multi-stock portfolio view
│   │
│   ├── models/                      # Pydantic v2 data models
│   │   ├── stock.py                 # StockQuote, FundamentalData, FundamentalScore, TechnicalSignals
│   │   ├── mutual_fund.py           # MFScheme, MFReturns, MFAnalysisResult
│   │   └── report.py               # AdvisoryReport
│   │
│   ├── storage/                     # Persistence
│   │   ├── db.py                    # SQLAlchemy ORM (SQLite)
│   │   └── cache.py                 # diskcache with 24h TTL
│   │
│   ├── reports/                     # Report generation
│   │   ├── html_generator.py        # Jinja2 HTML reports
│   │   ├── pdf_generator.py         # WeasyPrint PDF (optional)
│   │   └── templates/               # HTML templates
│   │
│   └── utils/
│       ├── helpers.py               # score_linear(), cagr(), format_inr(), nse_symbol()
│       ├── logger.py                # Rich logging
│       └── rate_limiter.py          # Token bucket rate limiter
│
└── tests/                           # pytest test suite
    ├── conftest.py                  # Fixtures: sample OHLCV, NAV, fundamentals
    ├── test_utils.py                # Helper function tests
    ├── test_analyzers/              # Unit tests (no network)
    ├── test_fetchers/               # Integration tests (@pytest.mark.integration)
    └── test_advisory/               # Advisory engine tests
```

## Scoring System

### Fundamental Score (0-100)

| Category | Weight | Key Metrics |
|---|---|---|
| Earnings Quality | 25% | Revenue CAGR, Profit CAGR, EPS growth, margins |
| Balance Sheet | 20% | D/E ratio, interest coverage, current ratio |
| Valuation | 20% | P/E vs sector, PEG, EV/EBITDA |
| Competitive Moat | 20% | ROE, ROCE, margin stability |
| Management | 15% | Promoter holding, pledge %, FII trends |

**Red flags** (5-point deduction each): declining margins, high debt, low ROE, promoter selling, auditor changes, etc.

**Ratings**: STRONG (80+), GOOD (65+), AVERAGE (45+), WEAK (30+), AVOID (<30)

### Technical Signals

- **Trend**: SMA 50/200 crossover, price vs 200-DMA, ADX strength
- **Momentum**: RSI (14), MACD histogram, Stochastic
- **Volatility**: Bollinger Bands, ATR
- **Signals**: Golden Cross, Death Cross, oversold/overbought alerts

### Mutual Fund Score

- Returns (1Y absolute, 3Y/5Y/10Y CAGR)
- Risk-adjusted: Sharpe ratio, Sortino ratio
- Alpha (Jensen's), Beta
- Max drawdown + recovery duration
- Rolling 3Y returns consistency

## Configuration

### config.yaml

Controls scoring weights, technical indicator periods, API rate limits, storage paths. Edit to customize thresholds.

### Environment Variables (.env)

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | No | Enables Claude LLM advisory reports |
| `NEWSAPI_KEY` | No | Enhanced news fetching |

## Testing

```bash
# Unit tests only (no network calls)
pytest tests/ -m "not integration"

# Integration tests (hits real APIs - yfinance, AMFI)
pytest tests/ -m integration

# All tests with verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=finsight --cov-report=html
```

## Data Sources

| Source | Data | Method |
|---|---|---|
| Yahoo Finance (`yfinance`) | Stock quotes, OHLCV, fundamentals, dividends | Python library |
| AMFI API | Mutual fund NAV, scheme search | Free REST API |
| World Bank API | GDP growth, inflation (macro) | Free REST API |
| MoneyControl / ET RSS | Financial news headlines | RSS feed parsing |
| NSE India | Index data, FII/DII (best-effort) | JSON endpoints |

## Key Design Decisions

- **`score_linear(value, bad, good)`** drives all 0-100 scoring - works bidirectionally, clamped
- **Data coverage %** shown alongside every score for transparency
- **yfinance is the primary data source** - reliable, free, no auth required
- **LLM advisory is optional** (`--skip-advisory` is default) - scores are useful standalone
- **None-safe** - all scoring handles missing data gracefully via `average_non_none()`
- **Rate limited** - token bucket rate limiter prevents API throttling

## Disclaimer

> All analysis generated by FinSight is for **educational and research purposes only**.
> It does not constitute financial advice. Investment in securities markets is subject
> to market risks. Past performance does not guarantee future results. Always consult
> a SEBI-registered investment advisor before making investment decisions.

## License

MIT
