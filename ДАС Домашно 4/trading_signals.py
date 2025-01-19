import pandas as pd


class SignalGenerator:
    def __init__(self, df):
        self.df = df
        self.signals = pd.Series(index=df.index, data='HOLD')

        # Define thresholds
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.stoch_oversold = 20
        self.stoch_overbought = 80

    def generate_signals(self):
        """Generate trading signals based on technical indicators."""
        # MACD conditions
        macd_buy = self.df['MACD'] > self.df['MACD Signal']
        macd_sell = self.df['MACD'] < self.df['MACD Signal']

        # Moving Average conditions
        sma_buy = self.df['EMA'] > self.df['SMMA']  # EMA above SMMA (Buy Signal)
        sma_sell = self.df['EMA'] < self.df['SMMA']  # EMA below SMMA (Sell Signal)

        # RSI conditions
        rsi_buy = self.df['RSI'] < self.rsi_oversold  # RSI below 30 (Oversold)
        rsi_sell = self.df['RSI'] > self.rsi_overbought  # RSI above 70 (Overbought)

        # Stochastic conditions
        stoch_buy = self.df['Stochastic Oscillator'] < self.stoch_oversold  # Stochastic below 20
        stoch_sell = self.df['Stochastic Oscillator'] > self.stoch_overbought  # Stochastic above 80

        # Price vs Moving Average conditions
        smma_buy = self.df['Last Transaction'] > self.df['SMMA']  # Price above SMMA (Bullish Signal)
        smma_sell = self.df['Last Transaction'] < self.df['SMMA']  # Price below SMMA (Bearish Signal)

        kama_buy = self.df['Last Transaction'] > self.df['KAMA']  # Price above KAMA (Bullish Signal)
        kama_sell = self.df['Last Transaction'] < self.df['KAMA']  # Price below KAMA (Bearish Signal)

        # Logical Buy Signal Logic (Consider SMMA and KAMA in the conditions)
        buy_conditions = (
            # Buy when RSI is oversold and there's a positive momentum signal (MACD buy or SMA buy)
                ((rsi_buy) & (macd_buy | sma_buy | smma_buy | kama_buy)) |
                # Or buy when Stochastic is oversold and there's a positive trend (MACD buy or SMA buy)
                ((stoch_buy) & (macd_buy | sma_buy | smma_buy | kama_buy))
        )

        # Logical Sell Signal Logic (Consider SMMA and KAMA in the conditions)
        sell_conditions = (
            # Sell when RSI is overbought and there's a negative momentum signal (MACD sell or SMA sell)
                ((rsi_sell) & (macd_sell | sma_sell | smma_sell | kama_sell)) |
                # Or sell when Stochastic is overbought and there's a negative trend (MACD sell or SMA sell)
                ((stoch_sell) & (macd_sell | sma_sell | smma_sell | kama_sell))
        )

        self.signals[buy_conditions] = 'BUY'
        self.signals[sell_conditions] = 'SELL'

        return self.signals