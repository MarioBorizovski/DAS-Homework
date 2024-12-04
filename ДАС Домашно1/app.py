from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd
import subprocess  # To run the scraper script

app = Flask(__name__)

# Path to the directory containing the CSV files
FILES_DIRECTORY = 'D://flaskProject/static'  # Adjust to your directory path

@app.route('/', methods=['GET'])
def index():
    files = os.listdir(FILES_DIRECTORY)
    return render_template('index.html', files=files, data=[], selected_file=None, latest_date=None)

@app.route('/read_file', methods=['POST'])
def read_file():
    selected_file = request.form['file_name']
    file_path = os.path.join(FILES_DIRECTORY, selected_file)

    if os.path.isfile(file_path):
        df = pd.read_csv(file_path, delimiter=',', decimal=',')

        df.columns = df.columns.str.strip()

        def clean_numeric(value):
            if isinstance(value, str):
                return value
            elif pd.isna(value) or value == "":
                return "0,00"
            return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        for column in ["Last Transaction", "Maximum", "Minimum", "Average", "Change", "Amount", "Total"]:
            df[column] = df[column].apply(clean_numeric)


        def clean_date(date):
            date = str(date)
            if len(date) == 7:  # e.g., "8112024" -> "08.11.2024"
                return f"{date[:2]}.{date[2:4]}.{date[4:]}"
            elif len(date) == 8:  # e.g., "08112024" -> "08.11.2024"
                return f"{date[:2]}.{date[2:4]}.{date[4:]}"
            return date

        df['Datum'] = df['Datum'].apply(clean_date)
        df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y')

        latest_date = df['Datum'].max().strftime('%d.%m.%Y')

        df = df.sort_values(by='Datum', ascending=False)
        data = df.to_dict(orient='records')

        return render_template('index.html', files=os.listdir(FILES_DIRECTORY), data=data,
                               selected_file=selected_file, latest_date=latest_date)

    return 'File not found or invalid.'

@app.route('/scrape', methods=['POST'])
def scrape():
    subprocess.run(["python", "domashno.py"])
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
