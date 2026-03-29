import pytest
import pandas as pd
import numpy as np
from finsight.analyzers.technical_analyzer import TechnicalAnalyzer


class TestTechnicalAnalyzer:
    def setup_method(self):
        self.analyzer = TechnicalAnalyzer()

    def test_analyze_produces_valid_output(self, sample_ohlcv):
        result = self.analyzer.analyze(sample_ohlcv, "TEST")
        assert result.symbol == "TEST"
        assert result.cmp > 0
        assert result.sma_50 is not None
        assert result.sma_200 is not None
        assert result.rsi_14 is not None
        assert 0 <= result.rsi_14 <= 100
        assert result.trend in ("BULLISH", "MILDLY BULLISH", "BEARISH", "MILDLY BEARISH", "NEUTRAL")
        assert result.momentum in ("OVERBOUGHT", "OVERSOLD", "NEUTRAL")

    def test_insufficient_data_raises(self):
        df = pd.DataFrame({
            "Open": [100] * 50,
            "High": [105] * 50,
            "Low": [95] * 50,
            "Close": [100] * 50,
            "Volume": [1000] * 50,
        }, index=pd.date_range("2024-01-01", periods=50))

        with pytest.raises(ValueError, match="at least 200"):
            self.analyzer.analyze(df, "SHORT")

    def test_signals_are_generated(self, sample_ohlcv):
        result = self.analyzer.analyze(sample_ohlcv, "TEST")
        assert len(result.signals) > 0

    def test_price_vs_200dma(self, sample_ohlcv):
        result = self.analyzer.analyze(sample_ohlcv, "TEST")
        assert result.price_vs_200dma_pct is not None

    def test_bollinger_bands_order(self, sample_ohlcv):
        result = self.analyzer.analyze(sample_ohlcv, "TEST")
        if result.bbands_upper and result.bbands_lower:
            assert result.bbands_upper > result.bbands_lower
            assert result.bbands_middle is not None

    def test_macd_values(self, sample_ohlcv):
        result = self.analyzer.analyze(sample_ohlcv, "TEST")
        assert result.macd_line is not None
        assert result.macd_signal is not None

    def test_relative_strength_with_benchmark(self, sample_ohlcv, sample_benchmark_df):
        # Truncate benchmark to match stock data length
        result = self.analyzer.analyze(sample_ohlcv, "TEST", sample_benchmark_df)
        assert result.relative_strength_vs_nifty is not None

    def test_relative_strength_without_benchmark(self, sample_ohlcv):
        result = self.analyzer.analyze(sample_ohlcv, "TEST", None)
        assert result.relative_strength_vs_nifty is None
