import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
import os
import subprocess
from config import Config
from data_processor import DataProcessor
from trading_signals import SignalGenerator
from os import environ


app = Flask(__name__)


@app.route('/')
def index():
    files = os.listdir(Config.FILES_DIRECTORY)
    return render_template('index.html', files=files)


@app.route('/read_file', methods=['POST'])
def read_file():
    selected_file = request.form['file_name']
    if not selected_file.endswith('.csv'):
        return "Invalid file type. Only CSV files are allowed.", 400
    return redirect(url_for('table', file_name=selected_file))


@app.route('/table')
def table():
    files = os.listdir(Config.FILES_DIRECTORY)
    selected_file = request.args.get('file_name')
    window = request.args.get('window', Config.DEFAULT_WINDOW)

    if not selected_file:
        return 'No file selected.'

    file_path = os.path.join(Config.FILES_DIRECTORY, selected_file)
    if not os.path.isfile(file_path):
        return 'File not found.'

    try:
        df = pd.read_csv(file_path, delimiter=',', decimal=',')
        df.columns = df.columns.str.strip()

        if len(df) < 2:
            return 'Insufficient data for calculations.'

        window_size = Config.WINDOW_MAP.get(window, Config.DEFAULT_WINDOW_SIZE)

        # Process data and generate signals
        processor = DataProcessor(df, window_size)
        df = processor.process()

        signal_generator = SignalGenerator(df)
        df['Signal'] = signal_generator.generate_signals()

        df = df.fillna(0)
        latest_date = df['Datum'].max().strftime('%d.%m.%Y')
        df = df.sort_values(by='Datum', ascending=False)
        data = df.to_dict(orient='records')

        return render_template('table.html', files=files, data=data,
                               selected_file=selected_file, latest_date=latest_date,
                               window=window)
    except Exception as e:
        return f'Error processing file: {str(e)}'


@app.route('/scrape', methods=['POST'])
def scrape():
    subprocess.run(["python", "scrape.py"])
    return redirect(url_for('index'))


@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    port = int(environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)