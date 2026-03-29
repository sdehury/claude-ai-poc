from typing import Optional


def nse_symbol(ticker: str) -> str:
    """Append .NS suffix for yfinance NSE stock lookup.

    Index symbols (starting with ^) are returned as-is.
    """
    ticker = ticker.strip().upper()
    if ticker.startswith("^"):
        return ticker
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        return f"{ticker}.NS"
    return ticker


def cagr(start_value: float, end_value: float, years: float) -> Optional[float]:
    """Compute Compound Annual Growth Rate in percentage.

    Returns None if inputs are invalid (negative values, zero years).
    """
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return None
    return ((end_value / start_value) ** (1.0 / years) - 1) * 100


def score_linear(value: Optional[float], bad: float, good: float) -> Optional[float]:
    """Map a metric value linearly to a 0-100 score.

    Works bidirectionally:
    - If good > bad: higher values score better (e.g., ROE: bad=0, good=25)
    - If good < bad: lower values score better (e.g., D/E: bad=2.0, good=0.0)

    Returns None if value is None. Clamped to [0, 100].
    """
    if value is None:
        return None
    if good == bad:
        return 50.0
    score = (value - bad) / (good - bad) * 100
    return max(0.0, min(100.0, score))


def average_non_none(scores: list[Optional[float]], default: float = 50.0) -> float:
    """Average a list of scores, ignoring None values.

    Returns default if all values are None.
    """
    valid = [s for s in scores if s is not None]
    if not valid:
        return default
    return sum(valid) / len(valid)


def data_coverage(values: list[Optional[object]]) -> float:
    """Return percentage of non-None values in a list."""
    if not values:
        return 0.0
    non_none = sum(1 for v in values if v is not None)
    return (non_none / len(values)) * 100


def format_inr(amount: Optional[float]) -> str:
    """Format a number as INR with Indian numbering (lakhs, crores)."""
    if amount is None:
        return "N/A"
    if abs(amount) >= 1e7:
        return f"Rs.{amount / 1e7:,.2f} Cr"
    if abs(amount) >= 1e5:
        return f"Rs.{amount / 1e5:,.2f} L"
    return f"Rs.{amount:,.2f}"


def format_pct(value: Optional[float], decimals: int = 2) -> str:
    """Format a percentage value."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"
