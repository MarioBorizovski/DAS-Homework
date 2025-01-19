import pandas as pd
import ta
from ta.trend import SMAIndicator, EMAIndicator, WMAIndicator

from app_functions import clean_numeric, clean_date
from indicators import SmoothedMovingAverageIndicator, KaufmanAdaptiveMovingAverageIndicator


class DataProcessor:
    def __init__(self, df, window_size):
        # Create explicit copy to avoid warnings
        self.df = df.copy()
        self.window_size = window_size

    def process(self):
        self._clean_data()
        self._calculate_indicators()
        self._round_indicators()
        return self.df

    def _clean_data(self):
        numeric_columns = ["Last Transaction", "Maximum", "Minimum", "Average",
                           "Change", "Amount", "Total"]

        for column in numeric_columns:
            self.df[column] = self.df[column].apply(clean_numeric)

        self.df['Datum'] = self.df['Datum'].apply(clean_date)
        self.df['Datum'] = pd.to_datetime(self.df['Datum'], format='%d.%m.%Y')
        self.df['Datum'] = self.df['Datum'].dt.date
        self.df = self.df.drop_duplicates(subset=['Datum'])

    def _calculate_indicators(self):
        # RSI
        self.df.loc[:, 'RSI'] = ta.momentum.RSIIndicator(
            self.df['Last Transaction'], window=self.window_size).rsi()

        # Stochastic
        self.df.loc[:, 'Stochastic Oscillator'] = ta.momentum.StochasticOscillator(
            high=self.df['Maximum'], low=self.df['Minimum'],
            close=self.df['Last Transaction'], window=self.window_size).stoch()

        # MACD
        macd = ta.trend.MACD(self.df['Last Transaction'])
        self.df.loc[:, 'MACD'] = macd.macd()
        self.df.loc[:, 'MACD Signal'] = macd.macd_signal()

        # Awesome Oscillator
        self.df.loc[:, 'Awesome Oscillator'] = ta.momentum.awesome_oscillator(
            high=self.df['Maximum'],
            low=self.df['Minimum'],
            window1=5,
            window2=34
        )

        # CCI
        self.df.loc[:, 'CCI'] = ta.trend.CCIIndicator(
            high=self.df['Maximum'],
            low=self.df['Minimum'],
            close=self.df['Last Transaction'],
            window=20
        ).cci()

        # Moving Averages
        self._calculate_moving_averages()

    def _calculate_moving_averages(self):
        self.df.loc[:, 'SMA'] = SMAIndicator(
            self.df['Last Transaction'], window=self.window_size).sma_indicator()
        self.df.loc[:, 'EMA'] = EMAIndicator(
            self.df['Last Transaction'], window=self.window_size).ema_indicator()
        self.df.loc[:, 'WMA'] = WMAIndicator(
            self.df['Last Transaction'], window=self.window_size).wma()
        self.df.loc[:, 'SMMA'] = SmoothedMovingAverageIndicator(
            self.df['Last Transaction'], window=self.window_size).smma()
        self.df.loc[:, 'KAMA'] = KaufmanAdaptiveMovingAverageIndicator(
            self.df['Last Transaction'], window=self.window_size).kama()

    def _round_indicators(self):
        indicators = ['RSI', 'Stochastic Oscillator', 'MACD', 'MACD Signal',
                     'Awesome Oscillator', 'CCI', 'SMA', 'EMA', 'WMA', 'SMMA', 'KAMA']
        for indicator in indicators:
            if indicator in self.df.columns:
                self.df.loc[:, indicator] = self.df[indicator].round(2)

        self.df = self.df.fillna(0)