# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FinSight** is a Python-based long-term investment research platform (5-10 year horizon) for Indian equities and mutual funds. It fetches real financial data, runs fundamental/technical/macro analysis with validated scoring, and can produce LLM-powered advisory reports.

## Architecture

Four-layer pipeline: **Data Fetchers** -> **Analysis Engine** -> **LLM Advisory** -> **Report Generator**

- **Orchestrator** (`finsight/orchestrator.py`): Pipeline coordinator that chains fetch -> analyze -> advise -> report
- **CLI** (`main.py`): typer-based CLI with `analyze-stock`, `analyze-mf`, `search-mf`, `history` commands
- **Fetchers** (`finsight/fetchers/`): yfinance (primary equity data), AMFI API (MF NAV), NSE (best-effort), World Bank (macro), RSS (news). All inherit from `base_fetcher.py` with rate limiting.
- **Analyzers** (`finsight/analyzers/`): Fundamental scoring (weighted 0-100), technical indicators (pandas-ta), MF risk-return metrics (Sharpe, Sortino, Alpha, Beta), VADER sentiment, macro/sector scoring
- **Advisory** (`finsight/advisory/`): Claude API integration with fallback to score-based reports when LLM unavailable
- **Storage** (`finsight/storage/`): SQLite via SQLAlchemy + diskcache for 24h caching
- **Reports** (`finsight/reports/`): Jinja2 HTML templates + WeasyPrint PDF generation

## Build & Run Commands

```bash
pip install -r requirements.txt

# Equity analysis (--skip-advisory is default, use --with-advisory for LLM reports)
python main.py analyze-stock RELIANCE INFY TCS

# Mutual fund analysis
python main.py analyze-mf 122639

# Search MF schemes
python main.py search-mf "parag parikh"

# View analysis history
python main.py history

# Run unit tests (no network)
pytest tests/ -m "not integration"

# Run integration tests (hits real APIs)
pytest tests/ -m integration

# Run all tests
pytest tests/ -v
```

## Key Design Decisions

- **`score_linear(value, bad, good)`** in `finsight/utils/helpers.py` drives all 0-100 scoring. Works bidirectionally, clamped.
- **Fundamental scoring** uses weighted categories: Earnings Quality (25%), Balance Sheet (20%), Valuation (20%), Moat (20%), Management (15%). 7 red flag conditions deduct 5 points each.
- **yfinance is the primary data source** for equities. Index symbols (^NSEI) are passed as-is, stock symbols get `.NS` suffix appended. Some fields (ROCE, promoter holding) are unavailable from yfinance -- scores handle None gracefully via `average_non_none()`.
- **Data coverage %** is shown alongside every score so users know how many metrics were actually available.
- **LLM advisory is optional** (`--skip-advisory` default). The system produces useful scores, signals, bull/bear points without it.
- **MF overlap analysis** uses Jaccard similarity. Holdings data requires manual input (no free API provides it).
- Config in `config.yaml`; secrets via `.env` file (copy from `.env.example`).

## Tech Stack

Python 3.11+, pandas, numpy, pydantic v2, SQLAlchemy, pandas-ta, yfinance, httpx, VADER sentiment, Anthropic SDK, typer, Rich, Jinja2, pytest
