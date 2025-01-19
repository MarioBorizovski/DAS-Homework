import pandas as pd
import ta
from ta.trend import SMAIndicator, EMAIndicator, WMAIndicator


class BaseIndicator:
    def __init__(self, close):
        self.close = close


class SmoothedMovingAverageIndicator(BaseIndicator):
    def __init__(self, close, window=14):
        super().__init__(close)
        self.window = window

    def smma(self):
        close_series = pd.Series(self.close)
        smma = pd.Series(index=close_series.index, dtype='float64')
        first_valid = self.window - 1
        smma.iloc[first_valid] = close_series.iloc[0:self.window].mean()

        for i in range(first_valid + 1, len(close_series)):
            smma.iloc[i] = (smma.iloc[i - 1] * (self.window - 1) + close_series.iloc[i]) / self.window

        return smma


class KaufmanAdaptiveMovingAverageIndicator(BaseIndicator):
    def __init__(self, close, window=10, fast_ema=2, slow_ema=30):
        super().__init__(close)
        self.window = window
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema

    def kama(self):
        close_series = pd.Series(self.close)
        change = abs(close_series - close_series.shift(self.window))
        volatility = abs(close_series - close_series.shift(1)).rolling(window=self.window).sum()

        er = pd.Series(0, index=close_series.index, dtype='float64')
        mask = volatility != 0
        er[mask] = change[mask] / volatility[mask]

        fastest = 2.0 / (self.fast_ema + 1)
        slowest = 2.0 / (self.slow_ema + 1)
        sc = (er * (fastest - slowest) + slowest) ** 2

        kama = pd.Series(index=close_series.index, dtype='float64')
        kama.iloc[self.window] = close_series.iloc[0:self.window].mean()

        for i in range(self.window + 1, len(close_series)):
            kama.iloc[i] = kama.iloc[i - 1] + sc.iloc[i] * (close_series.iloc[i] - kama.iloc[i - 1])

        return kama.ffill()