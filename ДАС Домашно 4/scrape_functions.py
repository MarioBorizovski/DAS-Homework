import numpy as np
import requests
from bs4 import BeautifulSoup
import os
import pandas as pd

def get_codes():
    response = requests.get("https://www.mse.mk/mk/stats/symbolhistory/kmb")
    soup = BeautifulSoup(response.text, 'html.parser')
    codes = soup.find("select", attrs={"id": "Code"}).text
    filtered_codes = []

    def contains_number(string):
        return any(char.isdigit() for char in string)

    for code in codes.split("\n"):
        if contains_number(code):
            continue
        else:
            filtered_codes.append(code)

    return filtered_codes


def is_scraped(code):
    if os.path.exists("static/tables/" + code + ".csv"):
        return True
    else:
        return False


def clean_nulls(df):
    df.replace("", np.nan, inplace=True)
    df['Minimum'] = df['Minimum'].fillna(df['Last Transaction'])
    df['Maximum'] = df['Maximum'].fillna(df['Last Transaction'])

    return df
