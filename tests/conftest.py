import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from finsight.models.stock import FundamentalData


@pytest.fixture
def strong_stock_fundamentals():
    """A fundamentally strong company."""
    return FundamentalData(
        symbol="STRONGCO",
        pe_ratio=22,
        pb_ratio=3.5,
        roe=22.0,
        roce=25.0,
        debt_to_equity=30.0,
        current_ratio=1.8,
        interest_coverage=8.0,
        revenue_growth_3y_cagr=18.0,
        profit_growth_3y_cagr=20.0,
        eps_growth_5y_cagr=17.0,
        dividend_yield=1.5,
        promoter_holding=65.0,
        promoter_holding_change_qoq=0.5,
        ev_ebitda=15.0,
        peg_ratio=1.2,
        net_profit_margin=18.0,
        free_cash_flow=5000000000,
    )


@pytest.fixture
def weak_stock_fundamentals():
    """A fundamentally weak company."""
    return FundamentalData(
        symbol="WEAKCO",
        pe_ratio=85,
        pb_ratio=8.0,
        roe=3.0,
        roce=4.0,
        debt_to_equity=250.0,
        current_ratio=0.6,
        interest_coverage=1.0,
        revenue_growth_3y_cagr=2.0,
        profit_growth_3y_cagr=-5.0,
        eps_growth_5y_cagr=-3.0,
        dividend_yield=0.0,
        promoter_holding=20.0,
        promoter_holding_change_qoq=-4.0,
        ev_ebitda=45.0,
        peg_ratio=4.0,
        net_profit_margin=2.0,
        free_cash_flow=-1000000000,
    )


@pytest.fixture
def sparse_fundamentals():
    """A company with very limited data (only P/E available)."""
    return FundamentalData(
        symbol="SPARSECO",
        pe_ratio=25,
    )


@pytest.fixture
def sample_ohlcv():
    """Generate 500 days of synthetic uptrending OHLCV data."""
    np.random.seed(42)
    dates = pd.bdate_range(end=datetime.now().date(), periods=500)
    n = len(dates)

    # Uptrending with noise
    base = 1000
    trend = np.linspace(0, 300, n)
    noise = np.random.normal(0, 15, n).cumsum()
    close = base + trend + noise
    close = np.maximum(close, 100)  # Floor at 100

    df = pd.DataFrame({
        "Open": close * (1 + np.random.uniform(-0.01, 0.01, n)),
        "High": close * (1 + np.random.uniform(0, 0.02, n)),
        "Low": close * (1 - np.random.uniform(0, 0.02, n)),
        "Close": close,
        "Volume": np.random.randint(100000, 5000000, n),
    }, index=dates)

    return df


@pytest.fixture
def sample_nav_df():
    """Generate synthetic NAV history for a mutual fund."""
    np.random.seed(123)
    dates = pd.bdate_range(end=datetime.now().date(), periods=2000)
    n = len(dates)

    # Growing NAV with volatility
    daily_returns = np.random.normal(0.0004, 0.012, n)  # ~10% annual return
    nav = 100 * np.cumprod(1 + daily_returns)

    df = pd.DataFrame({"nav": nav}, index=dates)
    return df


@pytest.fixture
def sample_benchmark_df():
    """Generate synthetic benchmark (Nifty) OHLCV data."""
    np.random.seed(456)
    dates = pd.bdate_range(end=datetime.now().date(), periods=2000)
    n = len(dates)

    daily_returns = np.random.normal(0.0003, 0.011, n)  # ~8% annual return
    close = 15000 * np.cumprod(1 + daily_returns)

    df = pd.DataFrame({
        "Open": close * 0.999,
        "High": close * 1.005,
        "Low": close * 0.995,
        "Close": close,
        "Volume": np.random.randint(1000000, 50000000, n),
    }, index=dates)

    return df
