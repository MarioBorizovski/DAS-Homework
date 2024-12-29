from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd
import ta
from ta.trend import SMAIndicator, EMAIndicator, WMAIndicator
import subprocess
from app_functions import *
import numpy as np



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

        # Calculate change and volatility
        change = abs(close_series - close_series.shift(self.window))
        volatility = abs(close_series - close_series.shift(1)).rolling(window=self.window).sum()

        # Efficiency Ratio (ER)
        er = pd.Series(0, index=close_series.index, dtype='float64')  # Default to 0
        mask = volatility != 0
        er[mask] = change[mask] / volatility[mask]

        # Smoothing Constant (SC)
        fastest = 2.0 / (self.fast_ema + 1)
        slowest = 2.0 / (self.slow_ema + 1)
        sc = (er * (fastest - slowest) + slowest) ** 2

        # Initialize KAMA
        kama = pd.Series(index=close_series.index, dtype='float64')
        kama.iloc[self.window] = close_series.iloc[0:self.window].mean()  # Use the average of the first `window`

        # Iterative KAMA Calculation
        for i in range(self.window + 1, len(close_series)):
            kama.iloc[i] = kama.iloc[i - 1] + sc.iloc[i] * (close_series.iloc[i] - kama.iloc[i - 1])

        return kama.ffill()  # Forward-fill to handle NaN


def generate_trading_signals(df):
    signals = pd.Series(index=df.index, data='HOLD')

    rsi_oversold = 30
    rsi_overbought = 70
    stoch_oversold = 20
    stoch_overbought = 80

    macd_buy = df['MACD'] > df['MACD Signal']
    macd_sell = df['MACD'] < df['MACD Signal']

    sma_buy = df['EMA'] > df['SMMA']  # EMA above SMMA (Buy Signal)
    sma_sell = df['EMA'] < df['SMMA']  # EMA below SMMA (Sell Signal)

    rsi_buy = df['RSI'] < rsi_oversold  # RSI below 30 (Oversold)
    rsi_sell = df['RSI'] > rsi_overbought  # RSI above 70 (Overbought)

    stoch_buy = df['Stochastic Oscillator'] < stoch_oversold  # Stochastic below 20
    stoch_sell = df['Stochastic Oscillator'] > stoch_overbought  # Stochastic above 80

    smma_buy = df['Last Transaction'] > df['SMMA']  # Price above SMMA (Bullish Signal)
    smma_sell = df['Last Transaction'] < df['SMMA']  # Price below SMMA (Bearish Signal)

    kama_buy = df['Last Transaction'] > df['KAMA']  # Price above KAMA (Bullish Signal)
    kama_sell = df['Last Transaction'] < df['KAMA']  # Price below KAMA (Bearish Signal)

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

    signals[buy_conditions] = 'BUY'
    signals[sell_conditions] = 'SELL'

    return signals



app = Flask(__name__)

FILES_DIRECTORY = 'static/tables/'


@app.route('/', methods=['GET'])
def index():
    files = os.listdir(FILES_DIRECTORY)
    return render_template('index.html', files=files)


@app.route('/read_file', methods=['POST'])
def read_file():
    selected_file = request.form['file_name']

    # Check if the selected file has a .csv extension
    if not selected_file.endswith('.csv'):
        return "Invalid file type. Only CSV files are allowed.", 400

    # Redirect to the table view with the selected file name
    return redirect(url_for('table', file_name=selected_file))


@app.route('/table', methods=['GET'])
def table():
    files = os.listdir(FILES_DIRECTORY)
    selected_file = request.args.get('file_name')
    window = request.args.get('window', '1d')

    if selected_file:
        file_path = os.path.join(FILES_DIRECTORY, selected_file)

        if os.path.isfile(file_path):
            df = pd.read_csv(file_path, delimiter=',', decimal=',')
            df.columns = df.columns.str.strip()

            for column in ["Last Transaction", "Maximum", "Minimum", "Average", "Change", "Amount", "Total"]:
                df[column] = df[column].apply(clean_numeric)

            df['Datum'] = df['Datum'].apply(clean_date)
            df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y')
            df['Datum'] = df['Datum'].dt.date
            df = df.drop_duplicates(subset=['Datum'])

            if len(df) < 2:
                return 'Insufficient data for calculations.'

            window_map = {'1d': 1, '1w': 14, '1m': 30}
            window_size = window_map.get(window, 14)

            df['RSI'] = ta.momentum.RSIIndicator(df['Last Transaction'], window=window_size).rsi()
            df['Stochastic Oscillator'] = ta.momentum.StochasticOscillator(
                high=df['Maximum'], low=df['Minimum'], close=df['Last Transaction'], window=window_size).stoch()

            macd_indicator = ta.trend.MACD(df['Last Transaction'])
            df['MACD'] = macd_indicator.macd()
            df['MACD Signal'] = macd_indicator.macd_signal()

            df['Awesome Oscillator'] = ta.momentum.AwesomeOscillatorIndicator(
                high=df['Maximum'], low=df['Minimum']).awesome_oscillator()

            df['CCI'] = ta.trend.CCIIndicator(df['Maximum'], df['Minimum'], df['Last Transaction'], window=20).cci()
            df['SMA'] = SMAIndicator(df['Last Transaction'], window=window_size).sma_indicator()
            df['EMA'] = EMAIndicator(df['Last Transaction'], window=window_size).ema_indicator()
            df['WMA'] = WMAIndicator(df['Last Transaction'], window=window_size).wma()
            df['SMMA'] = SmoothedMovingAverageIndicator(df['Last Transaction'], window=window_size).smma()
            df['KAMA'] = KaufmanAdaptiveMovingAverageIndicator(df['Last Transaction'], window=window_size).kama()

            # Generate trading signals
            df['Signal'] = generate_trading_signals(df)

            df['RSI'] = df['RSI'].round(2)
            df['Stochastic Oscillator'] = df['Stochastic Oscillator'].round(2)
            df['MACD'] = df['MACD'].round(2)
            df['MACD Signal'] = df['MACD Signal'].round(2)
            df['Awesome Oscillator'] = df['Awesome Oscillator'].round(2)
            df['CCI'] = df['CCI'].round(2)
            df['SMA'] = df['SMA'].round(2)
            df['EMA'] = df['EMA'].round(2)
            df['WMA'] = df['WMA'].round(2)
            df['SMMA'] = df['SMMA'].round(2)
            df['KAMA'] = df['KAMA'].round(2)

            df = df.fillna(0)

            latest_date = df['Datum'].max().strftime('%d.%m.%Y')
            df = df.sort_values(by='Datum', ascending=False)
            data = df.to_dict(orient='records')

            return render_template('table.html', files=files, data=data, selected_file=selected_file,
                                   latest_date=latest_date, window=window)

    return 'File not found or invalid.'


@app.route('/scrape', methods=['POST'])
def scrape():
    subprocess.run(["python", "domashno.py"])
    return redirect(url_for('index'))


@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True)