import pandas as pd

def clean_date(date):
    date = str(date)
    if len(date) == 7:  # e.g., "8112024" -> "08.11.2024"
        return f"{date[:2]}.{date[2:4]}.{date[4:]}"
    elif len(date) == 8:  # e.g., "08112024" -> "08.11.2024"
        return f"{date[:2]}.{date[2:4]}.{date[4:]}"
    return date


def clean_numeric(value):
    if isinstance(value, str):
        value = value.replace(".", "").replace(",", ".")  # Replace commas with periods for proper float conversion
        try:
            return float(value)
        except ValueError:
            return 0.0  # Return 0 if the value cannot be converted to float
    elif pd.isna(value) or value == "":
        return 0.0
    return value