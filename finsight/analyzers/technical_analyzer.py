import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Optional

from finsight.models.stock import TechnicalSignals
from finsight.utils.logger import get_logger

logger = get_logger(__name__)

MIN_ROWS = 200  # Minimum data points for meaningful technical analysis


class TechnicalAnalyzer:
    """Technical analysis using pandas-ta indicators."""

    def analyze(
        self,
        df: pd.DataFrame,
        symbol: str,
        nifty_df: Optional[pd.DataFrame] = None,
    ) -> TechnicalSignals:
        """Run full technical analysis on OHLCV data.

        Args:
            df: OHLCV DataFrame with DatetimeIndex (minimum 200 rows)
            symbol: Stock symbol for labeling
            nifty_df: Optional Nifty 50 OHLCV for relative strength calculation
        """
        if len(df) < MIN_ROWS:
            raise ValueError(
                f"Need at least {MIN_ROWS} data points, got {len(df)}"
            )

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        cmp = float(close.iloc[-1])

        # Trend indicators
        sma_50 = ta.sma(close, length=50)
        sma_200 = ta.sma(close, length=200)
        ema_20 = ta.ema(close, length=20)

        # Momentum indicators
        rsi = ta.rsi(close, length=14)
        macd_result = ta.macd(close, fast=12, slow=26, signal=9)
        adx_result = ta.adx(high, low, close, length=14)

        # Volatility indicators
        bbands = ta.bbands(close, length=20, std=2)

        # Extract latest values safely
        sma_50_val = self._last_valid(sma_50)
        sma_200_val = self._last_valid(sma_200)
        ema_20_val = self._last_valid(ema_20)
        rsi_val = self._last_valid(rsi)

        # MACD components
        macd_line_val = None
        macd_signal_val = None
        macd_hist_val = None
        if macd_result is not None and not macd_result.empty:
            cols = macd_result.columns
            macd_line_val = self._last_valid(macd_result[cols[0]])
            macd_signal_val = self._last_valid(macd_result[cols[2]])
            macd_hist_val = self._last_valid(macd_result[cols[1]])

        # ADX
        adx_val = None
        if adx_result is not None and not adx_result.empty:
            adx_col = [c for c in adx_result.columns if "ADX" in c and "DM" not in c]
            if adx_col:
                adx_val = self._last_valid(adx_result[adx_col[0]])

        # Bollinger Bands
        bb_upper = bb_middle = bb_lower = None
        if bbands is not None and not bbands.empty:
            cols = bbands.columns
            bb_lower = self._last_valid(bbands[cols[0]])
            bb_middle = self._last_valid(bbands[cols[1]])
            bb_upper = self._last_valid(bbands[cols[2]])

        # Derived signals
        trend = self._determine_trend(cmp, sma_50_val, sma_200_val, adx_val)
        momentum = self._determine_momentum(rsi_val)
        golden_cross = self._detect_cross(sma_50, sma_200, cross_type="golden")
        death_cross = self._detect_cross(sma_50, sma_200, cross_type="death")

        # Price vs 200-DMA
        price_vs_200dma = None
        if sma_200_val and sma_200_val > 0:
            price_vs_200dma = ((cmp - sma_200_val) / sma_200_val) * 100

        # Relative strength vs Nifty (6-month)
        rel_strength = self._compute_relative_strength(df, nifty_df)

        # Generate human-readable signals
        signals = self._generate_signals(
            cmp, sma_50_val, sma_200_val, rsi_val,
            macd_hist_val, adx_val, price_vs_200dma,
            golden_cross, death_cross, bb_upper, bb_lower,
        )

        return TechnicalSignals(
            symbol=symbol.upper(),
            cmp=round(cmp, 2),
            sma_50=self._round(sma_50_val),
            sma_200=self._round(sma_200_val),
            ema_20=self._round(ema_20_val),
            rsi_14=self._round(rsi_val),
            macd_line=self._round(macd_line_val),
            macd_signal=self._round(macd_signal_val),
            macd_histogram=self._round(macd_hist_val),
            bbands_upper=self._round(bb_upper),
            bbands_middle=self._round(bb_middle),
            bbands_lower=self._round(bb_lower),
            adx=self._round(adx_val),
            trend=trend,
            momentum=momentum,
            golden_cross=golden_cross,
            death_cross=death_cross,
            price_vs_200dma_pct=self._round(price_vs_200dma),
            relative_strength_vs_nifty=self._round(rel_strength),
            signals=signals,
        )

    @staticmethod
    def _last_valid(series: Optional[pd.Series]) -> Optional[float]:
        if series is None or series.empty:
            return None
        last = series.iloc[-1]
        if pd.isna(last):
            valid = series.dropna()
            if valid.empty:
                return None
            return float(valid.iloc[-1])
        return float(last)

    @staticmethod
    def _round(val: Optional[float], decimals: int = 2) -> Optional[float]:
        if val is None:
            return None
        return round(val, decimals)

    @staticmethod
    def _determine_trend(
        cmp: float,
        sma_50: Optional[float],
        sma_200: Optional[float],
        adx: Optional[float],
    ) -> str:
        if sma_50 is None or sma_200 is None:
            return "NEUTRAL"

        strong_trend = adx is not None and adx > 25

        if cmp > sma_50 > sma_200:
            return "BULLISH" if strong_trend else "MILDLY BULLISH"
        elif cmp < sma_50 < sma_200:
            return "BEARISH" if strong_trend else "MILDLY BEARISH"
        else:
            return "NEUTRAL"

    @staticmethod
    def _determine_momentum(rsi: Optional[float]) -> str:
        if rsi is None:
            return "NEUTRAL"
        if rsi > 70:
            return "OVERBOUGHT"
        elif rsi < 30:
            return "OVERSOLD"
        return "NEUTRAL"

    @staticmethod
    def _detect_cross(
        fast_ma: Optional[pd.Series],
        slow_ma: Optional[pd.Series],
        cross_type: str = "golden",
        lookback: int = 5,
    ) -> bool:
        """Detect SMA cross in the last N trading days."""
        if fast_ma is None or slow_ma is None:
            return False

        diff = fast_ma - slow_ma
        diff = diff.dropna()

        if len(diff) < lookback + 1:
            return False

        recent = diff.iloc[-(lookback + 1):]

        for i in range(1, len(recent)):
            prev = recent.iloc[i - 1]
            curr = recent.iloc[i]
            if cross_type == "golden" and prev <= 0 and curr > 0:
                return True
            elif cross_type == "death" and prev >= 0 and curr < 0:
                return True

        return False

    @staticmethod
    def _compute_relative_strength(
        stock_df: pd.DataFrame,
        nifty_df: Optional[pd.DataFrame],
        months: int = 6,
    ) -> Optional[float]:
        """Compute relative strength vs Nifty over N months."""
        if nifty_df is None or nifty_df.empty:
            return None

        trading_days = months * 21
        if len(stock_df) < trading_days or len(nifty_df) < trading_days:
            return None

        stock_return = (
            (stock_df["Close"].iloc[-1] / stock_df["Close"].iloc[-trading_days]) - 1
        ) * 100
        nifty_return = (
            (nifty_df["Close"].iloc[-1] / nifty_df["Close"].iloc[-trading_days]) - 1
        ) * 100

        return stock_return - nifty_return

    @staticmethod
    def _generate_signals(
        cmp, sma_50, sma_200, rsi, macd_hist, adx,
        price_vs_200dma, golden_cross, death_cross,
        bb_upper, bb_lower,
    ) -> list[str]:
        signals = []

        # Price vs moving averages
        if sma_200 is not None:
            if cmp > sma_200:
                signals.append(f"Trading above 200-DMA ({price_vs_200dma:+.1f}%) — bullish")
            else:
                signals.append(f"Trading below 200-DMA ({price_vs_200dma:+.1f}%) — bearish")

        if sma_50 is not None and sma_200 is not None:
            if sma_50 > sma_200:
                signals.append("50-DMA above 200-DMA — bullish alignment")
            else:
                signals.append("50-DMA below 200-DMA — bearish alignment")

        # Cross events
        if golden_cross:
            signals.append("GOLDEN CROSS detected (50-DMA crossed above 200-DMA) — strong bullish signal")
        if death_cross:
            signals.append("DEATH CROSS detected (50-DMA crossed below 200-DMA) — strong bearish signal")

        # RSI
        if rsi is not None:
            if rsi > 70:
                signals.append(f"RSI at {rsi:.1f} — overbought, potential pullback")
            elif rsi < 30:
                signals.append(f"RSI at {rsi:.1f} — oversold, potential bounce")
            else:
                signals.append(f"RSI at {rsi:.1f} — neutral zone")

        # MACD
        if macd_hist is not None:
            if macd_hist > 0:
                signals.append("MACD histogram positive — bullish momentum")
            else:
                signals.append("MACD histogram negative — bearish momentum")

        # ADX
        if adx is not None:
            if adx > 25:
                signals.append(f"ADX at {adx:.1f} — strong trend")
            else:
                signals.append(f"ADX at {adx:.1f} — weak/no trend")

        # Bollinger Bands
        if bb_upper is not None and bb_lower is not None:
            if cmp > bb_upper:
                signals.append("Price above upper Bollinger Band — overextended")
            elif cmp < bb_lower:
                signals.append("Price below lower Bollinger Band — potential reversal zone")

        return signals
